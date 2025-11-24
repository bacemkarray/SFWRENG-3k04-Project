import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import butter, lfilter

class EgramViewer:
    def __init__(self, time, atrial, ventricular):
        self.time = time
        self.atrial = atrial
        self.ventricular = ventricular
        
        # User options
        self.show_atrial = True
        self.show_ventricular = False
        self.show_both = False
        self.gain = 1.0  # 0.5, 1, 2
        self.high_pass = False
        
        # Visualization window (seconds)
        self.window_length = 3.0
        self.index = 0
        
        # Precompute sampling rate
        self.dt = time[1] - time[0]
        self.samples_per_window = int(self.window_length / self.dt)

        # Setup plot
        self.fig, self.ax = plt.subplots()
        self.line_atrial, = self.ax.plot([], [], label="Atrial")
        self.line_vent, = self.ax.plot([], [], label="Ventricular")
        self.ax.set_xlim(0, self.window_length)
        self.ax.set_ylim(-5, 5)
        self.ax.legend()

    def apply_high_pass(self, signal):
        if not self.high_pass:
            return signal
        b, a = butter(1, 0.5, btype='high', fs=1/self.dt)
        return lfilter(b, a, signal)

    def select_signals(self, atrial, vent):
        atrial = atrial * self.gain
        vent = vent * self.gain

        atrial = self.apply_high_pass(atrial)
        vent = self.apply_high_pass(vent)

        return atrial, vent

    def update(self, frame):
        # Compute window indices
        start = self.index
        end = self.index + self.samples_per_window
        if end >= len(self.time):
            return

        t_win = self.time[start:end] - self.time[start]  # Relative time for plotting
        atrial_win, vent_win = self.select_signals(
            self.atrial[start:end],
            self.ventricular[start:end]
        )

        # Update selected channels
        if self.show_atrial or self.show_both:
            self.line_atrial.set_data(t_win, atrial_win)
        if self.show_ventricular or self.show_both:
            self.line_vent.set_data(t_win, vent_win)

        self.index += 2  # Controls scroll speed
        return self.line_atrial, self.line_vent

    def start(self):
        self.anim = FuncAnimation(self.fig, self.update, interval=30)
        plt.show()


# ---------------------
# Example Usage
# ---------------------
if __name__ == "__main__":
    t = np.linspace(0, 20, 10000)
    atrial_signal = np.sin(2 * np.pi * 3 * t) + 0.2*np.random.randn(len(t))
    ventricular_signal = np.sin(2 * np.pi * 1 * t) + 0.2*np.random.randn(len(t))

    viewer = EgramViewer(t, atrial_signal, ventricular_signal)
    viewer.show_atrial = True
    viewer.gain = 2.0
    viewer.high_pass = True

    viewer.start()
