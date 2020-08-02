from clients.remote_client.remote_client import RemoteInputInterface

class InputInterface(RemoteInputInterface):

    def __init__(self):
        super(InputInterface, self).__init__()
        self.name = "Remote Space Coaster Client"
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True
        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]


    def init_gui(self, frame):
        super(InputInterface, self).init_gui(frame)
        self.show_ride_selector(False)