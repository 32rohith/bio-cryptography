import numpy as np

class AdaptiveKalmanFilter:
    """
    A 4D Adaptive Kalman Filter for tracking position (x, y) and velocity (vx, vy).
    
    State Vector X: [x, y, vx, vy]^T
    
    The filter is tuned to track smooth human motion (intention), leaving 
    high-frequency tremor in the innovation residuals.
    """
    def __init__(self, dt=0.001):
        self.dt = dt
        
        # 1. State Vector [x, y, vx, vy]'
        self.x = np.zeros((4, 1))

        # 2. State Transition Matrix F (Constant Velocity Model)
        # x_new = x + vx*dt
        # vx_new = vx
        self.F = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        # 3. Measurement Matrix H (We observe x and y)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])

        # 4. Process Noise Covariance Q
        # Models uncertainty in the system model (e.g., changes in velocity/acceleration).
        # Lower values = trust model more (smoother). Higher = trust model less.
        # Tuned low to encourage smoothing of tremor.
        self.Q = np.eye(4) * 0.1 

        # 5. Measurement Noise Covariance R
        # Models uncertainty in the sensor.
        # Tuned higher relative to Q to treat high-frequency jitter as noise (tremor).
        self.R = np.eye(2) * 5.0

        # 6. Error Covariance Matrix P
        # Initial uncertainty.
        self.P = np.eye(4) * 1.0

    def predict(self):
        """
        Projects the state ahead of the measurement.
        x_k|k-1 = F * x_k-1|k-1
        P_k|k-1 = F * P_k-1|k-1 * F^T + Q
        """
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return self.x

    def update(self, measurement_x, measurement_y):
        """
        Updates the state with a new measurement (z_k).
        
        Args:
            measurement_x (float): Observed X coordinate.
            measurement_y (float): Observed Y coordinate.
            
        Returns:
            np.array: Innovation Residuals (y_k = z_k - H * x_k|k-1)
                      This contains the deviation from the smooth path (i.e., vibration/tremor).
        """
        # Measurement Vector z
        z = np.array([[measurement_x], [measurement_y]])

        # 1. Measurement Residual (Innovation) y = z - Hx
        # This is the "surprise" or the difference between observation and prediction.
        # For our use case, this residual is the TREMOR.
        y = z - np.dot(self.H, self.x)

        # 2. Kalman Gain K = P * H^T * inv(H * P * H^T + R)
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R  # Residual Covariance
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        # 3. Update State Estimate x = x + Ky
        self.x = self.x + np.dot(K, y)

        # 4. Update Error Covariance P = (I - KH)P
        I = np.eye(self.x.shape[0])
        self.P = np.dot((I - np.dot(K, self.H)), self.P)
        
        # Return the residuals (flattened to 1D array [res_x, res_y])
        return y.flatten()
