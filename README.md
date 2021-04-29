## Запуск
Для запуска следует импортировать в main
```python
from TrackBuilder.main import analytics
from TrackBuilder.jsonify_main import make_input_json
```
В тестовой среде для предварительной запаковки входных параметров в json
```
    :param track_boxes: входные боксы предсказанные детектором
    :param crop_coors: координаты лент
    :param height: высота кадра
    :param width: ширина кадра
    :param frame_number: номер кадра
    :return: упакованная json'ка с входными параметрами для функции analitics
```
```python
    analytics_input = make_input_json(track_boxes, crop_coors, height, width, frame_number)
    analytic_result = analytics(analytics_input, frame)
```
> В реальной системе только вызвать функцию, где:
```python
    analytic_result = analytics(analytics_input)
```
Входные параметры для функции analytics:
```
    :param analytics_input: json согласно схеме
            :param track_boxes: входные боксы предсказанные детектором
            :param crop_coors: координаты лент
            :param height: высота кадра
            :param width: ширина кадра
            :param frame_number: номер кадра
            :return: упакованная json'ка с входными параметрами для функции analitics
    :param frame: временный проброс кадра в модуль для отрисовки, в боевой сборке удалить
```
Выходные параметры это два json, для barrier detector и для command processor
```
        :param polygon: выходной полигон функции analitics
        :param frame_height: высота кадра
        :param frame_width: ширина кадра
        :param frame_number: номер кадра
    :return: упакованная json'ка для barrier detector'а

        :param switch: данные об изменении состояния стрелки
        :param frame_number: номер кадра
    :return: упакованная json"ка для command processor

```
## Калибровка
Для калибровки использовать файл config.json
требуется указать a_perspective_best, b_perspective_best,
это боксы в формате соответственно входным данным rail_boxes
первый является задетектированным боксом максимально отдаленным от поезда
второй - бокс находящийся непосредственно рядом с тепловозом
```python
{
    "a_perspective_best": [665, 0, 732, 19, 3],
    "b_perspective_best": [550, 624, 850, 720, 16]

}
```

## DOTENV

> в корне проекта создать файл .env. Этот файл является локальным и не попадает в репозиторий. Указывать только необходимые переменные.

```dotenv
TBDebug=1
TBDebug2=0
VIDEO=RTSP/test/win46rev.mp4
```

> в коде python делаем проверку переменной

```python
import os

if os.getenv(ENV_VARIABLE) == '1':
# debug code
```

* TBDebug [0||1] - отрисовка входных и выходных боксов
* TBDebug [0||1] - отрисовка входных и выходных боксов
* VIDEO=[path] - видео для модуля RTSP ('RTSP/test/win46rev.mp4')
