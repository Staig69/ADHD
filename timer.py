import winsound

class Timer:
    def __init__(self, work_mins=25, break_mins=5):
        self.work_duration = work_mins * 60
        self.break_duration = break_mins * 60

    def set_durations(self, work_mins, break_mins):
        self.work_duration = int(work_mins) * 60
        self.break_duration = int(break_mins) * 60

    def play_sound(self, event_type):
        if event_type == "work_start":
            winsound.Beep(1000, 400)
        elif event_type == "break_start":
            winsound.Beep(800, 600)
        elif event_type == "finish":
            winsound.Beep(1500, 300)
            winsound.Beep(2000, 500)