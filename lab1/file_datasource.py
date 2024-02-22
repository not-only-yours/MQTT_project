from csv import reader
from datetime import datetime
from domain.aggregated_data import AggregatedData
from domain.accelerometer import Accelerometer
from domain.gps import Gps

class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.accelerometer_file = None
        self.gps_file = None

    def startReading(self, *args, **kwargs):
        self.accelerometer_file = open(self.accelerometer_filename, 'r')
        self.gps_file = open(self.gps_filename, 'r')

    def stopReading(self, *args, **kwargs):
        if self.accelerometer_file:
            self.accelerometer_file.close()
        if self.gps_file:
            self.gps_file.close()

    def read(self) -> AggregatedData:
        if not self.accelerometer_file or not self.gps_file:
            raise ValueError("Files not opened. Call startReading before reading data.")

        while True:
            # Reset file position to beginning after skipping header
            self.accelerometer_file.seek(0)
            self.gps_file.seek(0)

            # Skipping header
            next(self.accelerometer_file)
            next(self.gps_file)

            try:
                accelerometer_data = next(reader(self.accelerometer_file))
                gps_data = next(reader(self.gps_file))
            except StopIteration:
                continue

            x, y, z = map(int, accelerometer_data)
            accelerometer_reading = Accelerometer(x, y, z)

            longitude, latitude = map(float, gps_data)
            gps_reading = Gps(longitude, latitude)

            timestamp = datetime.now()

            aggregated_data = AggregatedData(accelerometer=accelerometer_reading,
                                             gps=gps_reading,
                                             time=timestamp)

            return aggregated_data
