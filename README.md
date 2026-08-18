# Oscilloscope XY Graphics with SIGLENT SDG6052X

This project demonstrates how an arbitrary waveform generator, the **SIGLENT SDG6052X**, together with an oscilloscope operating in **X-Y mode**, can be used to generate mathematical figures, 2D vector graphics, and animated 3D objects.

The generator is controlled from **Python** using **PyVISA** and **SCPI commands**.

The oscilloscope used during development was a **HAMEG HM303-6**.

---

## Project idea

In X-Y mode, the oscilloscope does not use the normal time base.

Instead, the position of the beam on the screen is controlled by two independent signals:

```text
SIGLENT CH1  ->  X
SIGLENT CH2  ->  Y
```

At every instant, the generator outputs a pair of coordinates:

```text
X[n], Y[n]
```

These values determine the successive positions of the beam on the oscilloscope screen.

For example, a circle can be described by:

```text
X(t) = cos(t)
Y(t) = sin(t)
```

More complex figures can be generated from parametric equations, interpolated points, or projected 3D geometry.

---

# Features

The project was developed in several stages and currently includes:

- Lissajous figures,
- custom 2D parametric shapes,
- arbitrary waveform generation,
- 3D wireframe objects,
- rotating 3D animations,
- direct SCPI control of the waveform generator,
- TrueArb waveform playback,
- synchronized X/Y channel output.

---

# Lissajous figures

The first part of the project generates classical Lissajous figures using two sinusoidal signals.

The program allows control of:

- the `fx / fy` frequency ratio,
- phase shift,
- base frequency,
- display time of each figure.

Example frequency ratios:

```text
1 : 1
1 : 2
1 : 3
2 : 3
```

Example phase shifts:

```text
0°
45°
90°
135°
180°
```

For Lissajous figures, the generator directly operates in `SINE` mode.

---

# 2D shapes

The project also supports custom arbitrary waveforms.

Currently implemented examples include:

- heart,
- star,
- sphere-like wireframe,
- custom parametric shapes.

For example, the heart is generated from:

```text
x(t) = 16 sin³(t)

y(t) = 13 cos(t)
       - 5 cos(2t)
       - 2 cos(3t)
       - cos(4t)
```

The resulting coordinates are normalized to approximately:

```text
-1 ... +1
```

before being converted into data suitable for the waveform generator.

---

# Arbitrary waveform generation

For complex shapes, the X and Y coordinates are converted into signed 16-bit values:

```python
np.round(np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
```

This maps the normalized waveform approximately as follows:

```text
-1.0  ->  -32767
 0.0  ->       0
+1.0  ->  +32767
```

The resulting binary data is then transferred to the generator.

For example:

```text
CH1 -> SHAPE_X
CH2 -> SHAPE_Y
```

Binary waveform data is transmitted using:

```python
device.write_raw(...)
```

The generator is then configured to operate in:

```text
ARB / TrueArb
```

mode.

---

# 3D graphics

The project was later extended to basic 3D vector graphics.

A 3D object is represented as a set of points:

```text
[x, y, z]
```

These points are rotated in 3D space and then projected onto a 2D plane:

```text
3D coordinates
[x, y, z]

      |
      v

3D rotation

      |
      v

projection

      |
      v

2D coordinates
[X, Y]

      |
      v

CH1 + CH2
```

Although the oscilloscope still receives only X and Y signals, the transformed coordinates create the visual appearance of a three-dimensional object.

---

# Rotating cube

One of the first 3D animation experiments is a rotating cube.

The cube is defined by eight vertices:

```text
[-1, -1, -1]
[ 1, -1, -1]
[ 1,  1, -1]
[-1,  1, -1]

[-1, -1,  1]
[ 1, -1,  1]
[ 1,  1,  1]
[-1,  1,  1]
```

The program creates successive frames by changing the rotation angle.

Each frame is converted to X/Y coordinates and combined into an arbitrary waveform sequence.

---

# Rotating 3D cow

The most advanced example in the project is an **animated rotating 3D cow model**.

The model is embedded directly inside the Python source code, so no external file such as:

```text
cow.obj
```

is required.

The embedded model contains approximately:

```text
2903 vertices
5804 triangles in the original mesh
17413 points in the continuous drawing path
```

The model data is compressed using:

```text
Base85 + zlib
```

and decoded automatically when the program starts.

---

## 3D rendering process

For every animation frame, the program performs:

1. 3D rotation,
2. coordinate transformation,
3. perspective projection,
4. path extraction,
5. scaling,
6. generation of X and Y waveforms.

A simple perspective projection is used:

```text
perspective = CAMERA_DISTANCE / (CAMERA_DISTANCE - z)

X = x * perspective
Y = y * perspective
```

This gives the rotating model a visible sense of depth.

---

# Animation

The most important animation parameters can be adjusted directly in the source code.

Example:

```python
ROTATION_PERIOD = 6.0
ANIMATION_FPS = 20
TRACE_REPEATS = 3
ROTATION_DIRECTION = 1
```

Where:

```text
ROTATION_PERIOD
```

defines the time required for one full revolution,

```text
ANIMATION_FPS
```

defines the number of unique object positions generated per second,

and:

```text
TRACE_REPEATS
```

defines how many times each frame is redrawn before the next frame is displayed.

Repeating the same frame increases the effective refresh rate and helps reduce visible flicker on an analog oscilloscope.

---

# TrueArb mode

Complex graphics are played using the TrueArb mode of the SIGLENT generator.

Example configuration:

```python
C1:SRATE MODE,TARB,VALUE,<sample_rate>,INTER,LINE
C2:SRATE MODE,TARB,VALUE,<sample_rate>,INTER,LINE
```

The option:

```text
INTER,LINE
```

enables linear interpolation between consecutive points.

This is particularly useful for vector graphics because the generator can connect successive vertices with straight lines without requiring thousands of manually generated intermediate samples.

---

# Channel synchronization

Synchronization between both generator channels is critical in X-Y mode.

The project uses:

```text
EQPHASE
```

to synchronize CH1 and CH2.

Without proper synchronization, the coordinate pairs:

```text
X[n]
Y[n]
```

could become shifted in time relative to each other, causing visible distortion of the displayed figure.

---

# Hardware

The project was developed using:

- **SIGLENT SDG6052X** arbitrary waveform generator,
- **HAMEG HM303-6** analog oscilloscope,
- PC connected to the generator over LAN.

Connection diagram:

```text
PC
 |
 | LAN / VISA / SCPI
 |
SIGLENT SDG6052X
 |
 +---- CH1 ----------------> HAMEG CH I  (X)
 |
 +---- CH2 ----------------> HAMEG CH II (Y)
```

The oscilloscope must be configured in:

```text
X-Y mode
```

---

# Software requirements

The project requires Python 3 and the following libraries:

```text
numpy
pyvisa
```

Install them with:

```bash
pip install numpy pyvisa
```

Depending on the system configuration, a VISA implementation may also be required.

For example:

```bash
pip install pyvisa-py
```

or NI-VISA can be used.

---

# Generator configuration

Before running the scripts, set the correct VISA address of the waveform generator.

Example:

```python
GENERATOR_ADDRESS = "TCPIP0::192.168.98.52::inst0::INSTR"
```

or in the dedicated cow animation script:

```python
VISA_RESOURCE = "TCPIP0::192.168.98.52::inst0::INSTR"
```

The IP address should be changed to match your local network configuration.

---

# Running the project

Example:

```bash
python Figur_Lissajous.py
```

For the dedicated 3D cow animation:

```bash
python krowa_3d_sdg6052x.py
```

After connecting, the program verifies communication with:

```text
*IDN?
```

and then uploads the required waveforms to the generator.

---

# Project structure

```text
.
├── Figur_Lissajous.py
├── krowa_3d_sdg6052x.py
└── README.md
```

## `Figur_Lissajous.py`

Main experimental script containing:

- PyVISA communication,
- Lissajous figures,
- heart shape,
- star shape,
- cube,
- sphere-like wireframe,
- arbitrary waveform generation,
- rotating cube,
- X-Y animation experiments.

## `krowa_3d_sdg6052x.py`

Dedicated script for the rotating 3D cow.

It contains:

- embedded 3D model data,
- geometry decoding,
- X/Y/Z rotation matrices,
- perspective projection,
- complete animation generation,
- signed 16-bit waveform conversion,
- TrueArb waveform transfer,
- CH1 / CH2 synchronization.

---

# How it works

The general signal-processing path is:

```text
Python
   |
   v
mathematics / 3D geometry
   |
   v
X[n], Y[n]
   |
   v
16-bit arbitrary waveforms
   |
   v
SIGLENT SDG6052X
   |
   +------ CH1 = X
   |
   +------ CH2 = Y
   |
   v
Analog oscilloscope in X-Y mode
```

The project therefore turns a standard oscilloscope into a simple vector display controlled entirely from Python.

---

# Educational goals

The project is intended as an experimental and educational platform for learning about:

- waveform generators,
- SCPI communication,
- PyVISA,
- arbitrary waveform generation,
- parametric equations,
- vector graphics,
- coordinate systems,
- linear interpolation,
- 3D transformations,
- rotation matrices,
- perspective projection,
- digital-to-analog waveform playback,
- synchronization of measurement equipment.

---

# Project status

This is an experimental project and is still being developed.

Future work may include:

- additional 2D figures,
- more complex 3D models,
- smoother animations,
- improved vector path optimization,
- reduced flicker,
- interactive object control,
- real-time animation,
- automatic oscilloscope scaling,
- additional arbitrary waveform experiments.

Contributions and experiments are welcome.
