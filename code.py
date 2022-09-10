import time
import board
import array
import math

import audiobusio
from adafruit_circuitplayground import cp

# setup pixel for all
cp.pixels.auto_write = False
cp.pixels.brightness = 0.2

# TEMP SETUP
# Set these based on your ambient temperature in Celsius for best results!
minimum_temp = 29
maximum_temp = 35


def scale_range(value2):
    return int((value2 - minimum_temp) / (maximum_temp - minimum_temp) * 10)


# SETUP SOUND
PEAK_COLOR = (100, 0, 255)
# Number of total pixels - 10 build into Circuit Playground
NUM_PIXELS = 10

# Exponential scaling factor.
# Should probably be in range -10 .. 10 to be reasonable.
CURVE = 2
SCALE_EXPONENT = math.pow(10, CURVE * -0.1)

# Number of samples to read at once.
NUM_SAMPLES = 160
# Restrict value to be between floor and ceiling.


def constrain(value, floor, ceiling):
    return max(floor, min(value, ceiling))


# Scale input_value between output_min and output_max, exponentially.
def log_scale(input_value, input_min, input_max, output_min, output_max):
    normalized_input_value = (input_value - input_min) / (input_max - input_min)
    return output_min + math.pow(normalized_input_value, SCALE_EXPONENT) * (
        output_max - output_min
    )


# Remove DC bias before computing RMS.
def normalized_rms(values):
    minbuf = int(mean(values))
    samples_sum = sum(float(sample - minbuf) * (sample - minbuf) for sample in values)

    return math.sqrt(samples_sum / len(values))


def mean(values):
    return sum(values) / len(values)


def volume_color(volume):
    return 200, volume * (255 // NUM_PIXELS), 0


mic = audiobusio.PDMIn(
    board.MICROPHONE_CLOCK, board.MICROPHONE_DATA, sample_rate=16000, bit_depth=16
)


while True:

# RUN SWITCH
    while cp.switch:

        temp = scale_range(cp.temperature)
        far = cp.temperature * 1.8 + 32
        print(cp.temperature)
        print(int(temp))
        print((cp.temperature, cp.temperature * 1.8 + 32, temp))
        time.sleep(0.2)

        for i in range(10):
            if i <= temp:
                cp.pixels[i] = (0, 0, 155)
            else:
                cp.pixels[i] = (far, temp, 0)
        cp.pixels.show()
        time.sleep(0.05)

    else:

        # Main program

        # Record an initial sample to calibrate. Assume it's quiet when we start.
        samples = array.array("H", [0] * NUM_SAMPLES)
        mic.record(samples, len(samples))
        # Set lowest level to expect, plus a little.
        input_floor = normalized_rms(samples) + 10
        # OR: used a fixed floor
        # input_floor = 50
        # You might want to print the input_floor to help adjust other values.
        print(input_floor)

        # Corresponds to sensitivity: lower means more pixels light up with lower sound
        # Adjust this as you see fit.
        input_ceiling = input_floor + 500

        peak = 0
        mic.record(samples, len(samples))
        magnitude = normalized_rms(samples)
        # You might want to print this to see the values.
        print(magnitude)
        print((magnitude, input_floor))
        time.sleep(0.05)
        # Compute scaled logarithmic reading in the range 0 to NUM_PIXELS
        c = log_scale(
            constrain(magnitude, input_floor, input_ceiling),
            input_floor,
            input_ceiling,
            0,
            NUM_PIXELS,
        )

        # Light up pixels that are below the scaled and interpolated magnitude.
        cp.pixels.fill(0)
        for z in range(NUM_PIXELS):
            if z < c:
                cp.pixels[z] = volume_color(z)
            # Light up the peak pixel and animate it slowly dropping.
            if c >= peak:
                peak = min(c, NUM_PIXELS - 1)
            elif peak > 0:
                peak = peak - 1
            if peak > 0:
                cp.pixels[int(peak)] = PEAK_COLOR
        cp.pixels.show()
