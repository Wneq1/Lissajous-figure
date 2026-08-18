import pyvisa
import time
import numpy as np

GENERATOR_ADDRESS = "TCPIP0::192.168.98.52::inst0::INSTR"


dev = None
generator = None



def set_generator_parameters(device):

    try:
        device_id = device.query("*IDN?").strip()

        if device_id:
            print("Połączono z:", device_id)

            device.write("*RST")
            device.write("*CLS")
            device.write("SYST:BEEP")

            return True

        print("Przyrząd zwrócił pustą odpowiedź.")
        return False

    except pyvisa.errors.VisaIOError as error:
        print("Błąd PyVISA:", error)
        return False

def generate_figure(device, f_base, figures,delay_time):
    for n in range(len(figures)):
                first_figure = figures[n]
                ratio_x = first_figure[0]
                ratio_y = first_figure[1]
                phi = first_figure[2]

                f_x = f_base * ratio_x
                f_y = f_base * ratio_y

                print(f"Figura {n + 1}/{len(figures)} | fx/fy = {ratio_x}/{ratio_y} | phi = {phi}° | fx = {f_x} Hz | fy = {f_y} Hz")

                device.write(f"C1:BSWV WVTP,SINE,FRQ,{f_x}HZ,AMP,2V,OFST,0V,PHSE,0")
                device.write(f"C2:BSWV WVTP,SINE,FRQ,{f_y}HZ,AMP,2V,OFST,0V,PHSE,{phi}")

                time.sleep(delay_time)

def send_Lissajous_to_generator(device,f_base,delay_time,infinity_loop = False):

    figures = [
        # fx / fy = 1 / 1
        (1, 1, 0),
        (1, 1, 45),
        (1, 1, 90),
        (1, 1, 135),
        (1, 1, 180),

        # fx / fy = 1 / 2
        (1, 2, 0),
        (1, 2, 45),
        (1, 2, 90),
        (1, 2, 135),
        (1, 2, 180),

        # fx / fy = 1 / 3
        (1, 3, 0),
        (1, 3, 45),
        (1, 3, 90),
        (1, 3, 135),
        (1, 3, 180),

        # fx / fy = 2 / 3
        (2, 3, 0),
        (2, 3, 45),
        (2, 3, 90),
        (2, 3, 135),
        (2, 3, 180)
    ]

    device.write("C1:OUTP ON")
    device.write("C2:OUTP ON")
    try:
        if infinity_loop:
            while True:
                generate_figure(device, f_base, figures,delay_time)         

                    
        else:
            generate_figure(device, f_base, figures,delay_time)
    finally:
        device.write("C1:OUTP OFF")
        device.write("C2:OUTP OFF")

def heart(number_of_points):

    t = np.linspace(0, 2*np.pi, number_of_points)

    x = 16*np.sin(t)**3
    y = 13*np.cos(t)-5*np.cos(2*t)-2*np.cos(3*t)-np.cos(4*t)

    x_centered = x - (x.max() + x.min()) / 2
    y_centered = y - (y.max() + y.min()) / 2
    
    maximum = max(np.max(np.abs(x_centered)), np.max(np.abs(y_centered)))

    x_normalised = x_centered / maximum
    y_normalised = y_centered / maximum
    return x_normalised, y_normalised

def star(number_of_points):
    outer_radius = 1.0
    inner_radius = 0.381966 * outer_radius

    x = []
    y = []

    alfa_0 = 90

    for n in range(10):
        angle = alfa_0 + n * 36
        angle_rad = np.deg2rad(angle)

        if n % 2 == 0:
            radius = outer_radius
        else:
            radius = inner_radius

        x_point = radius * np.cos(angle_rad)
        y_point = radius * np.sin(angle_rad)

        x.append(x_point)
        y.append(y_point)

    # domknięcie listy wierzchołków
    x.append(x[0])
    y.append(y[0])

    x = np.array(x)
    y = np.array(y)

    # number_of_points - 1, bo ostatni punkt dodamy ręcznie jako domknięcie
    t = np.linspace(0, 10, number_of_points - 1, endpoint=False)

    segment = np.floor(t).astype(int)
    u = t - segment

    x_points = (1 - u) * x[segment] + u * x[segment + 1]
    y_points = (1 - u) * y[segment] + u * y[segment + 1]

    # dokładne domknięcie przebiegu
    x_points = np.append(x_points, x_points[0])
    y_points = np.append(y_points, y_points[0])

    return x_points, y_points

def cube(number_of_points):

    vertices = np.array([
        [-1, -1, -1],
        [ 1, -1, -1],
        [ 1,  1, -1],
        [-1,  1, -1],

        [-1, -1,  1],
        [ 1, -1,  1],
        [ 1,  1,  1],
        [-1,  1,  1]
    ])

    path = [
        0, 1, 2, 3, 0,
        4, 5, 1, 5,
        6, 2, 6,
        7, 3, 7,
        4, 0
    ]

    points_3d = vertices[path]

    x = points_3d[:, 0]
    y = points_3d[:, 1]
    z = points_3d[:, 2]

    angle_y = np.deg2rad(35)
    angle_x = np.deg2rad(25)

    x_rot = x * np.cos(angle_y) + z * np.sin(angle_y)
    z_rot = -x * np.sin(angle_y) + z * np.cos(angle_y)

    y_rot = y * np.cos(angle_x) - z_rot * np.sin(angle_x)

    t = np.linspace(0, len(x_rot) - 1, number_of_points - 1, endpoint=False)

    segment = np.floor(t).astype(int)
    u = t - segment

    x_points = (1 - u) * x_rot[segment] + u * x_rot[segment + 1]
    y_points = (1 - u) * y_rot[segment] + u * y_rot[segment + 1]

    x_points = np.append(x_points, x_points[0])
    y_points = np.append(y_points, y_points[0])

    maximum = max(np.max(np.abs(x_points)), np.max(np.abs(y_points)))

    x_points = x_points / maximum
    y_points = y_points / maximum

    return x_points, y_points

def ball(number_of_points):

    meridians = 12
    points_per_meridian = number_of_points // meridians

    x_points = []
    y_points = []
    z_points = []

    for n in range(meridians):

        phi = 2 * np.pi * n / meridians

        # raz północ -> południe, raz południe -> północ
        if n % 2 == 0:
            theta = np.linspace(0, np.pi, points_per_meridian)
        else:
            theta = np.linspace(np.pi, 0, points_per_meridian)

        x = np.sin(theta) * np.cos(phi)
        y = np.cos(theta)
        z = np.sin(theta) * np.sin(phi)

        x_points.extend(x)
        y_points.extend(y)
        z_points.extend(z)

    x_points = np.array(x_points)
    y_points = np.array(y_points)
    z_points = np.array(z_points)

    # ustawienie kuli pod kątem
    angle_y = np.deg2rad(30)
    angle_x = np.deg2rad(20)

    # obrót wokół Y
    x_rot = x_points * np.cos(angle_y) + z_points * np.sin(angle_y)
    z_rot = -x_points * np.sin(angle_y) + z_points * np.cos(angle_y)

    # obrót wokół X
    y_rot = y_points * np.cos(angle_x) - z_rot * np.sin(angle_x)

    maximum = max(np.max(np.abs(x_rot)), np.max(np.abs(y_rot)))

    x_rot = x_rot / maximum
    y_rot = y_rot / maximum

    return x_rot, y_rot

def generate_shape(device, samples, shapes, delay_time):

    trace_rate = 100

    for name, shape_function in shapes:

        x, y = shape_function(samples)

        print(f"Kształt: {name} | liczba próbek: {len(x)}")

        x_data = np.round(np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
        y_data = np.round(np.clip(y, -1, 1) * 32767).astype("<i2").tobytes()

        sample_rate = len(x) * trace_rate

        device.write("C1:OUTP OFF")
        device.write("C2:OUTP OFF")

        header_x = f"C1:WVDT WVNM,SHAPE_X,FREQ,{trace_rate},AMPL,2,OFST,0,PHASE,0,WAVEDATA,".encode("ascii")
        header_y = f"C2:WVDT WVNM,SHAPE_Y,FREQ,{trace_rate},AMPL,2,OFST,0,PHASE,0,WAVEDATA,".encode("ascii")

        device.write_raw(header_x + x_data)
        device.write_raw(header_y + y_data)

        device.write("C1:ARWV NAME,SHAPE_X")
        device.write("C2:ARWV NAME,SHAPE_Y")

        device.write("C1:BSWV WVTP,ARB")
        device.write("C2:BSWV WVTP,ARB")

        device.write(f"C1:SRATE MODE,TARB,VALUE,{sample_rate},INTER,LINE")
        device.write(f"C2:SRATE MODE,TARB,VALUE,{sample_rate},INTER,LINE")

        device.write("C1:OUTP ON")
        device.write("C2:OUTP ON")

        device.write("EQPHASE")

        time.sleep(delay_time)

def send_shape_to_generator(device,samples,delay_time,infinity_loop = False):
        shapes = [
        ("HEART", heart),
        ("STAR", star),
        ("CUBE", cube),
        ("BALL", ball)
        ]
        device.write("C1:OUTP ON")
        device.write("C2:OUTP ON")
        try:
            if infinity_loop:
                while True:
                    generate_shape(device,samples,shapes,delay_time)         

                        
            else:
                generate_shape(device,samples,shapes,delay_time)  
        finally:
            device.write("C1:OUTP OFF")
            device.write("C2:OUTP OFF")

def rotating_cube(number_of_points=200, angle_step=10, frame_repeats=5):

    vertices = np.array([
        [-1, -1, -1],
        [ 1, -1, -1],
        [ 1,  1, -1],
        [-1,  1, -1],

        [-1, -1,  1],
        [ 1, -1,  1],
        [ 1,  1,  1],
        [-1,  1,  1]
    ])

    path = [
        0, 1, 2, 3, 0,
        4, 5, 1, 5,
        6, 2, 6,
        7, 3, 7,
        4, 0
    ]

    points = vertices[path]

    all_x = []
    all_y = []

    for angle in range(0, 360, angle_step):

        angle = np.deg2rad(angle)

        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]

        # ============================================================
        # STAŁE USTAWIENIE SZEŚCIANU W 3D
        # ============================================================

        angle_y = np.deg2rad(35)
        angle_x = np.deg2rad(25)

        x_3d = x * np.cos(angle_y) + z * np.sin(angle_y)
        z_3d = -x * np.sin(angle_y) + z * np.cos(angle_y)

        y_3d = y * np.cos(angle_x) - z_3d * np.sin(angle_x)

        # ============================================================
        # OBRÓT CAŁEGO RZUTU
        # ============================================================

        x_rot = x_3d * np.cos(angle) - y_3d * np.sin(angle)
        y_rot = x_3d * np.sin(angle) + y_3d * np.cos(angle)

        t = np.linspace(0, len(x_rot) - 1, number_of_points, endpoint=False)

        segment = np.floor(t).astype(int)
        u = t - segment

        x_points = (1 - u) * x_rot[segment] + u * x_rot[segment + 1]
        y_points = (1 - u) * y_rot[segment] + u * y_rot[segment + 1]

        maximum = max(np.max(np.abs(x_points)), np.max(np.abs(y_points)))

        x_points = x_points / maximum
        y_points = y_points / maximum

        # ta sama klatka kilka razy
        for _ in range(frame_repeats):
            all_x.append(x_points)
            all_y.append(y_points)

    all_x = np.concatenate(all_x)
    all_y = np.concatenate(all_y)

    return all_x, all_y

def send_rotating_cube(device, number_of_points=200, angle_step=10, frame_repeats=5, fps=20, delay_time=20):

    x, y = rotating_cube(number_of_points, angle_step, frame_repeats)

    number_of_frames = len(range(0, 360, angle_step))

    x_data = np.round(np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    y_data = np.round(np.clip(y, -1, 1) * 32767).astype("<i2").tobytes()

    # każda klatka jest teraz rysowana frame_repeats razy
    sample_rate = number_of_points * frame_repeats * fps

    animation_frequency = fps / number_of_frames

    print(f"Klatki: {number_of_frames}")
    print(f"Powtórzeń jednej klatki: {frame_repeats}")
    print(f"FPS animacji: {fps}")
    print(f"Sample rate: {sample_rate} Sa/s")
    print(f"Czas obrotu: {number_of_frames / fps:.2f} s")

    device.write("C1:OUTP OFF")
    device.write("C2:OUTP OFF")

    header_x = f"C1:WVDT WVNM,CUBE_X,FREQ,{animation_frequency},AMPL,2,OFST,0,PHASE,0,WAVEDATA,".encode("ascii")
    header_y = f"C2:WVDT WVNM,CUBE_Y,FREQ,{animation_frequency},AMPL,2,OFST,0,PHASE,0,WAVEDATA,".encode("ascii")

    device.write_raw(header_x + x_data)
    device.write_raw(header_y + y_data)

    device.write("C1:ARWV NAME,CUBE_X")
    device.write("C2:ARWV NAME,CUBE_Y")

    device.write("C1:BSWV WVTP,ARB")
    device.write("C2:BSWV WVTP,ARB")

    device.write(f"C1:SRATE MODE,TARB,VALUE,{sample_rate},INTER,LINE")
    device.write(f"C2:SRATE MODE,TARB,VALUE,{sample_rate},INTER,LINE")

    device.write("C1:OUTP ON")
    device.write("C2:OUTP ON")

    device.write("EQPHASE")

    time.sleep(delay_time)

    device.write("C1:OUTP OFF")
    device.write("C2:OUTP OFF")

def rotating_cow(rotation_period=6.0, fps=20, trace_repeats=3):

    vertices, path = decode_cow()

    frames = int(rotation_period * fps)

    all_x = []
    all_y = []

    for frame in range(frames):

        angle = 2 * np.pi * frame / frames

        x, y = render_frame(vertices, path, angle)

        for _ in range(trace_repeats):
            all_x.append(x)
            all_y.append(y)

    all_x = np.concatenate(all_x)
    all_y = np.concatenate(all_y)

    maximum = max(
        np.max(np.abs(all_x)),
        np.max(np.abs(all_y))
    )

    all_x = all_x * 0.86 / maximum
    all_y = all_y * 0.86 / maximum

    sample_rate = len(all_x) / rotation_period

    return all_x, all_y, sample_rate

def send_rotating_cow(device, rotation_period=6.0, fps=20, trace_repeats=3, delay_time=20):

    x, y, sample_rate = rotating_cow(
        rotation_period,
        fps,
        trace_repeats
    )

    print(f"Liczba próbek: {len(x)}")
    print(f"Sample rate: {sample_rate:.0f} Sa/s")

    x_data = np.round(
        np.clip(x, -1, 1) * 32767
    ).astype("<i2").tobytes()

    y_data = np.round(
        np.clip(y, -1, 1) * 32767
    ).astype("<i2").tobytes()

    device.write("C1:OUTP OFF")
    device.write("C2:OUTP OFF")

    header_x = (
        f"C1:WVDT "
        f"WVNM,COW_X,"
        f"FREQ,{1 / rotation_period},"
        f"AMPL,4,"
        f"OFST,0,"
        f"PHASE,0,"
        f"WAVEDATA,"
    ).encode("ascii")

    header_y = (
        f"C2:WVDT "
        f"WVNM,COW_Y,"
        f"FREQ,{1 / rotation_period},"
        f"AMPL,4,"
        f"OFST,0,"
        f"PHASE,0,"
        f"WAVEDATA,"
    ).encode("ascii")

    print("Wysyłanie krowy X...")
    device.write_raw(header_x + x_data)

    print("Wysyłanie krowy Y...")
    device.write_raw(header_y + y_data)

    device.write("C1:ARWV NAME,COW_X")
    device.write("C2:ARWV NAME,COW_Y")

    device.write("C1:BSWV WVTP,ARB")
    device.write("C2:BSWV WVTP,ARB")

    device.write(
        f"C1:SRATE MODE,TARB,VALUE,{sample_rate},INTER,LINE"
    )

    device.write(
        f"C2:SRATE MODE,TARB,VALUE,{sample_rate},INTER,LINE"
    )

    device.write("C1:OUTP ON")
    device.write("C2:OUTP ON")

    device.write("EQPHASE")

    time.sleep(delay_time)

    device.write("C1:OUTP OFF")
    device.write("C2:OUTP OFF")

try:

    dev = pyvisa.ResourceManager()
    generator = dev.open_resource(GENERATOR_ADDRESS)

    if_dev_rdy = set_generator_parameters(generator)
    print(if_dev_rdy)

    if if_dev_rdy:
        
        time.sleep(5)
        send_rotating_cow(generator, 6.0, 20, 3, 30)

finally:

    if generator is not None:
        generator.close()

    if dev is not None:
        dev.close()