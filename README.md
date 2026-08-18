# Oscilloscope XY Graphics with SIGLENT SDG6052X

Projekt pokazuje możliwość wykorzystania generatora arbitralnego **SIGLENT SDG6052X** oraz oscyloskopu pracującego w trybie **X-Y** do generowania figur matematycznych, kształtów 2D oraz animowanych obiektów 3D.

Sterowanie generatorem odbywa się z poziomu **Pythona** przy wykorzystaniu biblioteki **PyVISA** oraz komend **SCPI**.

W projekcie używany był oscyloskop analogowy **HAMEG HM303-6**.

---

## Idea projektu

W trybie X-Y oscyloskop nie wykorzystuje klasycznej podstawy czasu.

Położenie plamki na ekranie określane jest przez dwa niezależne sygnały:

```text
SIGLENT CH1  ->  X
SIGLENT CH2  ->  Y
```

Dla każdej chwili generator dostarcza więc parę współrzędnych:

```text
X[n], Y[n]
```

które odpowiadają kolejnym punktom rysowanego kształtu.

Przykładowo okrąg może zostać opisany równaniami:

```text
X(t) = cos(t)
Y(t) = sin(t)
```

a bardziej skomplikowane figury mogą być tworzone poprzez dowolne funkcje parametryczne lub współrzędne wygenerowane na podstawie modelu 3D.

---

# Funkcjonalności

Projekt jest rozwijany etapami i obejmuje kilka rodzajów generowanych obrazów.

## Figury Lissajousa

Pierwszą częścią projektu są klasyczne figury Lissajousa generowane za pomocą dwóch przebiegów sinusoidalnych.

Program pozwala zmieniać:

- stosunek częstotliwości `fx / fy`,
- przesunięcie fazowe,
- częstotliwość bazową,
- czas prezentacji każdej figury.

Przykładowe konfiguracje:

```text
1 : 1
1 : 2
1 : 3
2 : 3
```

oraz fazy:

```text
0°
45°
90°
135°
180°
```

W tym przypadku generator pracuje bezpośrednio w trybie `SINE`.

---

## Kształty 2D

Program pozwala również generować własne przebiegi arbitralne.

Aktualnie zaimplementowane zostały m.in.:

- serce,
- gwiazda,
- kula / siatka sferyczna,
- własne przebiegi parametryczne.

Przykładowo serce generowane jest na podstawie równań:

```text
x(t) = 16 sin³(t)

y(t) = 13 cos(t)
       - 5 cos(2t)
       - 2 cos(3t)
       - cos(4t)
```

Współrzędne są następnie normalizowane do zakresu:

```text
-1 ... +1
```

i konwertowane do 16-bitowych próbek generatora.

---

# Przebiegi arbitralne

Dla bardziej skomplikowanych figur współrzędne `X` i `Y` są zamieniane na dane 16-bitowe:

```python
np.round(np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
```

Zakres:

```text
-1       -> około -32767
 0       -> 0
+1       -> około +32767
```

Następnie dane są przesyłane do generatora jako przebiegi arbitralne.

Przykładowo:

```text
CH1 -> SHAPE_X
CH2 -> SHAPE_Y
```

Do przesłania danych binarnych wykorzystywane jest:

```python
device.write_raw(...)
```

Generator jest następnie ustawiany w tryb:

```text
ARB / TrueArb
```

z interpolacją liniową pomiędzy kolejnymi punktami.

---

# Obiekty 3D

Projekt został rozszerzony również o podstawową grafikę 3D.

Obiekt jest najpierw definiowany jako zbiór punktów:

```text
[x, y, z]
```

następnie wykonywany jest obrót w przestrzeni 3D, a otrzymany model jest rzutowany na płaszczyznę:

```text
3D
[x, y, z]

   |
   v

obrót

   |
   v

projekcja

   |
   v

2D
[X, Y]

   |
   v

CH1 + CH2
```

Oscyloskop nadal otrzymuje wyłącznie dwie współrzędne, jednak dzięki odpowiedniej transformacji możliwe jest uzyskanie wrażenia trójwymiarowości.

---

## Obracający się sześcian

Jednym z pierwszych testów animacji 3D jest obracający się sześcian.

Model składa się z ośmiu wierzchołków:

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

Kolejne klatki powstają poprzez zmianę kąta obrotu.

Animacja nie jest przesyłana klatka po klatce przez sieć. Kolejne pozycje figury mogą zostać połączone w długi przebieg arbitralny, który następnie jest samodzielnie odtwarzany przez generator.

---

# Obracająca się krowa 3D

Najbardziej rozbudowanym przykładem projektu jest **animowany model krowy 3D**.

Model jest zapisany bezpośrednio w pliku Pythona, dlatego nie jest potrzebny zewnętrzny plik:

```text
cow.obj
```

Model zawiera:

```text
2903 wierzchołki
5804 trójkąty źródłowej siatki
17413 punktów ciągłej ścieżki
```

Dane modelu zostały skompresowane i zapisane w kodzie przy użyciu:

```text
Base85 + zlib
```

Po uruchomieniu są automatycznie dekodowane.

---

## Renderowanie krowy

Dla każdej klatki wykonywane są:

1. obrót modelu,
2. transformacja współrzędnych,
3. projekcja perspektywiczna,
4. wybór kolejnych punktów ścieżki,
5. skalowanie obrazu,
6. utworzenie przebiegów `X` oraz `Y`.

Zastosowana jest prosta projekcja perspektywiczna:

```text
perspective = CAMERA_DISTANCE / (CAMERA_DISTANCE - z)

X = x * perspective
Y = y * perspective
```

Dzięki temu model podczas obrotu zachowuje wrażenie przestrzenności.

---

## Animacja

Podstawowe parametry animacji można zmieniać bez modyfikowania pozostałej części programu.

Przykład:

```python
ROTATION_PERIOD = 6.0
ANIMATION_FPS = 20
TRACE_REPEATS = 3
ROTATION_DIRECTION = 1
```

gdzie:

```text
ROTATION_PERIOD
```

określa czas jednego pełnego obrotu,

```text
ANIMATION_FPS
```

określa liczbę różnych pozycji modelu generowanych na sekundę,

a:

```text
TRACE_REPEATS
```

określa, ile razy każda klatka jest ponownie kreślona przed przejściem do następnej.

Powtarzanie klatki zwiększa częstotliwość odświeżania obrazu na oscyloskopie i ogranicza widoczne migotanie.

---

# TrueArb

Do odtwarzania skomplikowanych przebiegów wykorzystywany jest tryb TrueArb generatora.

Przykładowa konfiguracja:

```python
C1:SRATE MODE,TARB,VALUE,<sample_rate>,INTER,LINE
C2:SRATE MODE,TARB,VALUE,<sample_rate>,INTER,LINE
```

Opcja:

```text
INTER,LINE
```

powoduje liniową interpolację pomiędzy kolejnymi punktami.

Ma to szczególne znaczenie przy rysowaniu modeli zbudowanych z odcinków, ponieważ generator może płynnie połączyć kolejne wierzchołki bez konieczności generowania ogromnej liczby punktów pośrednich.

---

# Synchronizacja kanałów

Przy pracy w trybie X-Y bardzo ważna jest synchronizacja obu kanałów.

Program wykorzystuje:

```text
EQPHASE
```

aby wyrównać fazę CH1 i CH2.

Bez prawidłowej synchronizacji współrzędne:

```text
X[n]
Y[n]
```

mogłyby zostać przesunięte względem siebie, powodując deformację obrazu.

---

# Wymagania

## Sprzęt

Projekt został przygotowany dla:

- generatora arbitralnego **SIGLENT SDG6052X**,
- oscyloskopu **HAMEG HM303-6** pracującego w trybie X-Y,
- komputera połączonego z generatorem poprzez LAN.

Schemat połączenia:

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

Oscyloskop należy przełączyć w tryb:

```text
X-Y
```

---

## Python

Wymagany jest Python 3 oraz biblioteki:

```text
numpy
pyvisa
```

Instalacja:

```bash
pip install numpy pyvisa
```

W zależności od konfiguracji komputera potrzebna jest również implementacja VISA, np. NI-VISA lub:

```bash
pip install pyvisa-py
```

---

# Konfiguracja generatora

Przed uruchomieniem programu należy ustawić prawidłowy adres VISA generatora.

Przykład:

```python
GENERATOR_ADDRESS = "TCPIP0::192.168.98.52::inst0::INSTR"
```

lub w programie krowy 3D:

```python
VISA_RESOURCE = "TCPIP0::192.168.98.52::inst0::INSTR"
```

Adres IP należy zmienić zgodnie z konfiguracją własnej sieci.

---

# Uruchomienie

Przykład uruchomienia programu:

```bash
python Figur_Lissajous.py
```

lub programu dedykowanego animowanej krowie:

```bash
python krowa_3d_sdg6052x.py
```

Po nawiązaniu komunikacji generator powinien odpowiedzieć na:

```text
*IDN?
```

Następnie program przesyła odpowiednie przebiegi i uruchamia oba kanały.

---

# Struktura projektu

```text
.
├── Figur_Lissajous.py
├── krowa_3d_sdg6052x.py
└── README.md
```

### `Figur_Lissajous.py`

Główny plik eksperymentalny zawierający m.in.:

- komunikację PyVISA,
- figury Lissajousa,
- serce,
- gwiazdę,
- sześcian,
- kulę,
- przebiegi ARB,
- animowany sześcian,
- eksperymenty z animacjami X-Y.

### `krowa_3d_sdg6052x.py`

Dedykowany program do generowania animowanego modelu krowy 3D.

Zawiera:

- zaszyty model 3D,
- dekodowanie geometrii,
- macierze obrotu X/Y/Z,
- projekcję perspektywiczną,
- generowanie pełnej animacji,
- konwersję przebiegu do 16 bit,
- wysyłanie danych TrueArb do generatora,
- synchronizację CH1 oraz CH2.

---

# Najważniejsza idea

Projekt pokazuje, że oscyloskop analogowy może zostać wykorzystany nie tylko do obserwacji przebiegów czasowych.

Po przełączeniu go w tryb X-Y generator arbitralny może pełnić rolę prostego systemu grafiki wektorowej:

```text
Python
   |
   v
matematyka / geometria 3D
   |
   v
X[n], Y[n]
   |
   v
16-bit TrueArb
   |
   v
SIGLENT SDG6052X
   |
   +-------- X
   |
   +-------- Y
   |
   v
oscyloskop XY
```

Pozwala to eksperymentować z:

- figurami matematycznymi,
- grafiką parametryczną,
- przebiegami arbitralnymi,
- transformacjami geometrycznymi,
- macierzami obrotu,
- projekcją 3D → 2D,
- animacją,
- sterowaniem aparaturą pomiarową przez SCPI.

---

# Status projektu

Projekt ma charakter eksperymentalny i edukacyjny.

Aktualnie rozwijane są kolejne metody generowania oraz animowania obrazów na oscyloskopie, a kod stanowi bazę do dalszych eksperymentów z grafiką wektorową, przebiegami arbitralnymi oraz sterowaniem aparaturą pomiarową z poziomu Pythona.
