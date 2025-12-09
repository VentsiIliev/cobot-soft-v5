# Модул за Процес на Нанасяне на Лепило - Изчерпателна Документация

**Версия:** 5.0  
**Дата:** Декември 2025  
**Път на Модула:** `/src/applications/glue_dispensing_application/glue_process`

---

## Съдържание

1. [Общ Преглед](#общ-преглед)
2. [Архитектура](#архитектура)
3. [Дизайн на Машината на Състоянията](#дизайн-на-машината-на-състоянията)
4. [Дефиниции на Състоянията](#дефиниции-на-състоянията)
5. [Контекст на Изпълнение](#контекст-на-изпълнение)
6. [Диаграми на Потока на Състоянията](#диаграми-на-потока-на-състоянията)
7. [Правила за Преход](#правила-за-преход)
8. [Контролер на Помпата](#контролер-на-помпата)
9. [Ръководство за Употреба](#ръководство-за-употреба)
10. [Конфигурация](#конфигурация)
11. [Обработка на Грешки](#обработка-на-грешки)
12. [Функционалност за Пауза/Възобновяване](#функционалност-за-паузавъзобновяване)
13. [Отстраняване на Грешки](#отстраняване-на-грешки)

---

## Общ Преглед

### Предназначение

Модулът за Процес на Нанасяне на Лепило управлява **пълния цикъл на операцията по нанасяне на лепило** използвайки архитектура на изпълнима машина на състоянията. Той координира движението на робота, контрола на помпата и синхронизацията на пътищата за прецизно нанасяне на лепило върху работни части.

### Какво Прави

1. **Управлява последователността на изпълнение** на множество пътища за нанасяне на лепило
2. **Координира движението на робота** към началните точки и по дефинирани траектории
3. **Контролира операциите на помпата** с настройки специфични за сегментите
4. **Регулира скоростта на помпата динамично** по време на нанасянето
5. **Обработва паузи и възобновявания** на средата на операцията
6. **Поддържа контекст на изпълнение** за проследяване на прогреса
7. **Осигурява синхронизация** между движението на робота и потока на лепилото
8. **Записва детайли за отстраняване на грешки** за всяко изпълнение на състояние

### Защо Съществува

Операциите по нанасяне на лепило изискват прецизен контрол за да:
- Осигурят консистентно приложение на лепило по сложни пътища
- Координират синхронно движението на робота и потока на помпата
- Поддържат точни настройки на скоростта специфични за всеки сегмент
- Позволяват възобновяване на операцията след прекъсване
- Минимизират отпадъка чрез прецизна дозировка
- Адаптират се към различни видове лепила и конфигурации на помпи

---

## Архитектура

### Основни Компоненти

```
glue_process/
├── glue_dispensing_operation.py          # Главен оркестратор на операцията
├── ExecutionContext.py                   # Контекст на изпълнение (съхранение на състояние)
├── PumpController.py                     # Логика за управление на помпата
├── dynamicPumpSpeedAdjustment.py        # Динамична регулация на скоростта
├── state_machine/                        # Дефиниции на машината на състоянията
│   ├── ExecutableStateMachine.py        # Базова изпълнима машина на състоянията
│   ├── GlueProcessState.py              # State enum и правила за преход
│   └── GlueProcessStateMachine.py       # Специфична имплементация
├── state_handlers/                       # Имплементации на обработчици на състояния
│   ├── start_state_handler.py           # STARTING състояние
│   ├── moving_to_first_point_state_handler.py  # MOVING_TO_FIRST_POINT
│   ├── initial_pump_boost_state_handler.py     # PUMP_INITIAL_BOOST
│   ├── start_pump_adjustment_thread_handler.py # STARTING_PUMP_ADJUSTMENT_THREAD
│   ├── sending_path_to_robot_state_handler.py  # SENDING_PATH_POINTS
│   ├── wait_for_path_completion_state_handler.py # WAIT_FOR_PATH_COMPLETION
│   ├── transition_between_paths_state_handler.py # TRANSITION_BETWEEN_PATHS
│   ├── compleated_state_handler.py      # COMPLETED състояние
│   ├── pause_operation.py               # Обработка на пауза
│   ├── resume_operation.py              # Обработка на възобновяване
│   └── stop_operation.py                # Обработка на спиране
└── debug/                                # Директория за отстраняване на грешки (генерирана)
    └── *.json                            # Файлове за отстраняване на контекста
```

### Дизайн Шаблон

**Изпълним Шаблон на Машина на Състоянията**
- Разделя логиката на състоянията от преходите между състоянията
- Всяко състояние е функция: `(ExecutionContext) → NextState`
- Контекстът съхранява целия прогрес и конфигурация на изпълнението
- Правилата за преход са декларативни и валидирани
- Обработчиците на състояния са тестваеми изолирано
- Callbacks за on_enter/on_exit за логване и отстраняване на грешки

---

## Дизайн на Машината на Състоянията

### Защо Машина на Състоянията?

Процесът на нанасяне на лепило е по същество **последователен** и **базиран на събития**:
- Всяка стъпка зависи от успешното завършване на предишните стъпки
- Операциите трябва да могат да бъдат паузирани и възобновявани
- Грешки могат да се появят по време на движението на робота или операциите на помпата
- Ясните преходи между състоянията правят поведението предвидимо
- Множествени пътища изискват итеративно изпълнение с контрол на състоянието

### Компоненти на Машината на Състоянията

#### 1. **State Enum** (`GlueProcessState`)
```python
class GlueProcessState(Enum):
    INITIALIZING = auto()
    IDLE = auto()
    STARTING = auto()
    MOVING_TO_FIRST_POINT = auto()
    EXECUTING_PATH = auto()
    PUMP_INITIAL_BOOST = auto()
    STARTING_PUMP_ADJUSTMENT_THREAD = auto()
    SENDING_PATH_POINTS = auto()
    WAIT_FOR_PATH_COMPLETION = auto()
    TRANSITION_BETWEEN_PATHS = auto()
    COMPLETED = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()
```

#### 2. **Обработчици на Състояния** (State Handlers)
Функции, които изпълняват логиката специфична за състоянието:
```python
def handle_starting_state(context: ExecutionContext) -> GlueProcessState:
    # Подготви пътя, настрой параметрите
    return GlueProcessState.MOVING_TO_FIRST_POINT
```

#### 3. **Контекст на Изпълнение** (`ExecutionContext`)
Съхранява всички променливи на състоянието:
- Данни за текущия път и точка
- Референции към услуги (робот, лепило)
- Състояние на помпата и настройки
- Флагове за пауза/възобновяване
- Референции към нишки за регулация на скоростта

#### 4. **Правила за Преход** (`GlueProcessTransitionRules`)
Дефинира валидните преходи между състоянията:
```python
{
    GlueProcessState.STARTING: {
        GlueProcessState.MOVING_TO_FIRST_POINT,
        GlueProcessState.PAUSED,
        GlueProcessState.STOPPED,
        GlueProcessState.ERROR
    }
}
```

---

## Дефиниции на Състоянията

### Състояния на Жизнения Цикъл

#### **INITIALIZING**
**Цел:** Начална инициализация на машината на състоянията  
**Вход:** Системата стартира  
**Обработка:**
- Зарежда конфигурацията на машината на състоянията
- Инициализира контекста на изпълнение
- Подготвя регистъра на състоянията

**Изход:** `IDLE`  
**Неуспешен Изход:** `ERROR`

---

#### **IDLE**
**Цел:** Състояние на готовност - изчаква команда за стартиране  
**Вход:** След инициализация или след завършване на операция  
**Обработка:**
- Изчаква команда `start()`
- Системата е готова за нова операция
- При сигнал за завършване, спира изпълнението на машината на състоянията

**Изход:** `STARTING` (когато се извика start)  
**Неуспешен Изход:** `ERROR`

---

### Състояния на Изпълнение

#### **STARTING**
**Цел:** Стартиране на изпълнението или зареждане на следващия път  
**Вход:** От `IDLE` или `TRANSITION_BETWEEN_PATHS`  
**Обработка:**
- Зарежда текущия път от списъка с пътища
- Извлича настройки специфични за сегмента
- Генерира події от интерполирани точки
- Подготвя параметри на помпата
- Проверява дали има още пътища за обработка

**Изход:**
- `MOVING_TO_FIRST_POINT` - нормален следващ път
- `COMPLETED` - няма повече пътища

**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

**Ключови Променливи:**
```python
context.current_path_index        # Индекс на текущия път
context.current_path              # Данни за текущия път
context.current_settings          # Настройки за този сегмент
```

---

#### **MOVING_TO_FIRST_POINT**
**Цел:** Позициониране на робота в началната точка на пътя  
**Вход:** От `STARTING`  
**Обработка:**
- Извлича първата точка от текущия път
- Изпраща команда на робота да се движи към тази точка
- Изчаква робота да достигне позицията
- При възобновяване, скача до запазената позиция

**Изход:** `EXECUTING_PATH`  
**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

**Поведение при Възобновяване:**
```python
if context.is_resuming:
    # Движи се към запазената точка
    target_index = context.current_point_index
else:
    # Движи се към първата точка
    target_index = 0
```

---

#### **EXECUTING_PATH**
**Цел:** Въвеждащо състояние за изпълнение на пътя  
**Вход:** От `MOVING_TO_FIRST_POINT`  
**Обработка:**
- Директен преход към `PUMP_INITIAL_BOOST`
- Не извършва обработка

**Изход:** `PUMP_INITIAL_BOOST`

---

#### **PUMP_INITIAL_BOOST**
**Цел:** Прилага начален boost на помпата за постигане на поток  
**Вход:** От `EXECUTING_PATH`  
**Обработка:**
- Стартира помпата с начални настройки
- Прилага ramp-up последователност:
  - Начална ramp скорост за кратка продължителност
  - Стъпки за увеличение на скоростта
- Изчаква помпата да достигне стабилен поток
- Използва настройки специфични за сегмента, ако са налични

**Изход:** `STARTING_PUMP_ADJUSTMENT_THREAD`  
**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

**Параметри на Помпата:**
```python
motor_speed                      # Целева скорост на помпата
initial_ramp_speed              # Начална скорост за boost
initial_ramp_speed_duration     # Продължителност на начален boost
forward_ramp_steps              # Стъпки за достигане на пълна скорост
```

---

#### **STARTING_PUMP_ADJUSTMENT_THREAD**
**Цел:** Стартиране на нишка за динамична регулация на скоростта  
**Вход:** От `PUMP_INITIAL_BOOST`  
**Обработка:**
- Създава нишка в заден план за мониторинг на скоростта на робота
- Регулира скоростта на помпата в реално време
- Поддържа консистентен поток на лепило при различни скорости на робота
- Използва event за сигнализиране на готовността

**Изход:** `SENDING_PATH_POINTS`  
**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

**Логика на Регулацията:**
```python
def dynamic_pump_adjustment(context):
    while context.robot_is_moving:
        current_speed = robot.get_current_speed()
        adjusted_pump_speed = calculate_pump_speed(current_speed)
        pump.set_speed(adjusted_pump_speed)
        time.sleep(adjustment_interval)
```

---

#### **SENDING_PATH_POINTS**
**Цел:** Изпращане на точки на пътя към контролера на робота  
**Вход:** От `STARTING_PUMP_ADJUSTMENT_THREAD`  
**Обработка:**
- Итерира през интерполирани точки на пътя
- Изпраща всяка точка към робота
- Поддържа индекс на текущата точка
- Позволява прекъсване за пауза/спиране

**Изход:** `WAIT_FOR_PATH_COMPLETION`  
**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

**Изпращане на Точки:**
```python
for point in path_points:
    robot_service.send_point(point)
    context.current_point_index += 1
    if context.paused or context.stopped:
        break
```

---

#### **WAIT_FOR_PATH_COMPLETION**
**Цел:** Изчаква робота да завърши текущия път  
**Вход:** От `SENDING_PATH_POINTS`  
**Обработка:**
- Мониторира състоянието на движението на робота
- Изчаква всички точки да бъдат изпълнени
- Спира нишката за регулация на помпата
- Изключва помпата след завършване (ако е конфигурирано)

**Изход:**
- `TRANSITION_BETWEEN_PATHS` - има още пътища
- `COMPLETED` - всички пътища са завършени

**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

---

#### **TRANSITION_BETWEEN_PATHS**
**Цел:** Подготовка за следващия път  
**Вход:** От `WAIT_FOR_PATH_COMPLETION`  
**Обработка:**
- Инкрементира индекса на пътя
- Спира помпата (ако `TURN_OFF_PUMP_BETWEEN_PATHS = True`)
- Изчиства състоянието на текущия път
- Проверява дали има повече пътища

**Изход:**
- `STARTING` - зарежда следващия път
- `COMPLETED` - няма повече пътища

**Неуспешен Изход:** `ERROR`, `PAUSED`, `STOPPED`

**Логика:**
```python
context.current_path_index += 1
if context.current_path_index < len(context.paths):
    return GlueProcessState.STARTING
else:
    return GlueProcessState.COMPLETED
```

---

### Състояния на Контрола

#### **PAUSED**
**Цел:** Временна пауза на операцията  
**Вход:** От всяко състояние на изпълнение  
**Обработка:**
- Записва текущото състояние и прогрес
- Спира помпата
- Спира нишката за регулация
- Запазва контекста за възобновяване

**Изход:**
- `STARTING` - възобновява изпълнението
- `STOPPED` - спира операцията
- `IDLE` - отказ

**Запазване на Прогреса:**
```python
context.paused_from_state = current_state
context.save_progress(path_index, point_index)
```

---

#### **STOPPED**
**Цел:** Изрично спиране на операцията  
**Вход:** От всяко състояние на изпълнение или `PAUSED`  
**Обработка:**
- Спира помпата
- Спира нишките
- Изчиства контекста на изпълнение
- Маркира операцията като спряна

**Изход:**
- `COMPLETED` - почиства и завършва
- `IDLE` - връща се в готовност

---

#### **COMPLETED**
**Цел:** Успешно завършване на операцията  
**Вход:** От `TRANSITION_BETWEEN_PATHS` или след последния път  
**Обработка:**
- Спира всички активни нишки
- Изключва помпата
- Задейства callback за завършване
- Маркира операцията като завършена

**Изход:** `IDLE`

**Логика за Завършване:**
```python
context.operation_just_completed = True
context.state_machine.transition(GlueProcessState.IDLE)
# IDLE обработчикът вижда флага и спира изпълнението
```

---

#### **ERROR**
**Цел:** Обработка на грешки  
**Вход:** От всяко състояние при възникване на грешка  
**Обработка:**
- Логва грешката
- Спира помпата
- Спира нишките
- Позволява възстановяване или reset

**Изход:**
- `IDLE` - възстановяване
- `INITIALIZING` - пълен reset
- `ERROR` - остава в грешка

---

## Контекст на Изпълнение

### ExecutionContext Класа

Съхранява всички състояния и конфигурация за изпълнението:

```python
class ExecutionContext:
    # Данни за пътя
    paths: List[Path]                    # Всички пътища за изпълнение
    current_path: Path                   # Текущ път
    current_path_index: int              # Индекс на текущия път
    current_point_index: int             # Индекс на текущата точка
    target_point_index: int              # Целева точка за движение
    
    # Референции към услуги
    service: GlueService                 # Услуга за лепило
    robot_service: RobotService          # Услуга за робот
    pump_controller: PumpController      # Контролер на помпата
    
    # Конфигурация
    spray_on: bool                       # Дали да се пръска лепило
    glue_type: str                       # Адрес на типа лепило
    current_settings: dict               # Настройки на сегмента
    
    # Управление на състоянието
    state_machine: ExecutableStateMachine # Референция към машината на състоянията
    paused_from_state: GlueProcessState  # Състояние преди пауза
    is_resuming: bool                    # Флаг за възобновяване
    
    # Управление на нишки
    pump_thread: Thread                  # Нишка за регулация на помпата
    pump_ready_event: Event              # Event за синхронизация
    
    # Състояние на помпата
    motor_started: bool                  # Дали помпата е стартирана
    generator_started: bool              # Дали генераторът е стартиран
    generator_to_glue_delay: float       # Забавяне между генератор и лепило
```

### Методи на Контекста

#### **reset()**
```python
def reset(self):
    # Нулира всички полета към начални стойности
    self.current_path_index = 0
    self.current_point_index = 0
    self.is_resuming = False
    # ... нулира всички останали полета
```

#### **save_progress(path_index, point_index)**
```python
def save_progress(self, path_index: int, point_index: int):
    # Записва прогреса за възобновяване след пауза
    self.current_path_index = path_index
    self.current_point_index = point_index
```

#### **has_valid_context()**
```python
def has_valid_context(self) -> bool:
    # Проверява дали контекстът има валидни данни за изпълнение
    return self.paths is not None and len(self.paths) > 0
```

#### **to_debug_dict()**
```python
def to_debug_dict(self) -> dict:
    # Сериализира контекста за debug изход
    return {
        "current_path_index": self.current_path_index,
        "current_point_index": self.current_point_index,
        "state": str(self.state_machine.state),
        # ... всички релевантни полета
    }
```

---

## Диаграми на Потока на Състоянията

### Основен Поток на Изпълнение

```
┌─────────────────┐
│  INITIALIZING   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│      IDLE       │◄──────────────────────┐
└────────┬────────┘                       │
         │ start()                        │
         v                                │
┌─────────────────┐                       │
│    STARTING     │◄──────────┐           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
┌─────────────────┐           │           │
│  MOVING_TO_     │           │           │
│  FIRST_POINT    │           │           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
┌─────────────────┐           │           │
│ EXECUTING_PATH  │           │           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
┌─────────────────┐           │           │
│ PUMP_INITIAL_   │           │           │
│     BOOST       │           │           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
┌─────────────────┐           │           │
│ STARTING_PUMP_  │           │           │
│ ADJUSTMENT_     │           │           │
│    THREAD       │           │           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
┌─────────────────┐           │           │
│ SENDING_PATH_   │           │           │
│    POINTS       │           │           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
┌─────────────────┐           │           │
│ WAIT_FOR_PATH_  │           │           │
│  COMPLETION     │           │           │
└────────┬────────┘           │           │
         │                    │           │
         v                    │           │
     [Още пътища?]            │           │
         │                    │           │
    ┌────┴────┐               │           │
    │         │               │           │
   ДА        НЕ               │           │
    │         │               │           │
    v         v               │           │
┌────────┐ ┌──────────┐       │           │
│TRANSIT-│ │COMPLETED │───────┘           │
│ION_    │ └──────────┘                   │
│BETWEEN │                                │
│_PATHS  │                                │
└───┬────┘                                │
    │                                     │
    └─────────────────────────────────────┘
```

### Поток на Пауза/Възобновяване

```
[Всяко Състояние на Изпълнение]
         │
         │ pause()
         v
┌─────────────────┐
│     PAUSED      │
│                 │
│ Записва:        │
│ - Състояние     │
│ - path_index    │
│ - point_index   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
 resume()  stop()
    │         │
    v         v
┌────────┐ ┌─────────┐
│STARTING│ │ STOPPED │
│        │ └────┬────┘
│(Resume)│      │
└────────┘      v
                ┌──────────┐
                │COMPLETED │
                └──────────┘
```

### Поток на Обработка на Грешки

```
[Всяко Състояние]
         │
         │ При грешка
         v
┌─────────────────┐
│     ERROR       │
│                 │
│ - Логва грешка  │
│ - Спира помпа   │
│ - Спира нишки   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
 recover() reset()
    │         │
    v         v
┌────────┐ ┌──────────────┐
│  IDLE  │ │INITIALIZING  │
└────────┘ └──────────────┘
```

---

## Правила за Преход

### Пълна Таблица на Преходите

| От Състояние | Към Състояния | Условие |
|-------------|---------------|---------|
| **INITIALIZING** | IDLE | Успешна инициализация |
| | ERROR | Грешка при инициализация |
| **IDLE** | STARTING | Извикана е start() |
| | ERROR | Системна грешка |
| **STARTING** | MOVING_TO_FIRST_POINT | Пътят е зареден |
| | COMPLETED | Няма пътища |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка при зареждане на пътя |
| **MOVING_TO_FIRST_POINT** | EXECUTING_PATH | Робот достигнал позиция |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка при движение |
| **EXECUTING_PATH** | PUMP_INITIAL_BOOST | Автоматичен преход |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Системна грешка |
| **PUMP_INITIAL_BOOST** | STARTING_PUMP_ADJUSTMENT_THREAD | Помпа готова |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка на помпата |
| **STARTING_PUMP_ADJUSTMENT_THREAD** | SENDING_PATH_POINTS | Нишка стартирана |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка при стартиране на нишка |
| **SENDING_PATH_POINTS** | WAIT_FOR_PATH_COMPLETION | Всички точки изпратени |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка при изпращане |
| **WAIT_FOR_PATH_COMPLETION** | TRANSITION_BETWEEN_PATHS | Път завършен, има още |
| | COMPLETED | Път завършен, последен |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка при изпълнение |
| **TRANSITION_BETWEEN_PATHS** | STARTING | Повече пътища |
| | COMPLETED | Няма повече пътища |
| | PAUSED | Заявена пауза |
| | STOPPED | Заявено спиране |
| | ERROR | Грешка при преход |
| **PAUSED** | STARTING | Възобновяване |
| | STOPPED | Спиране от пауза |
| | IDLE | Отказ |
| | PAUSED | Остава в пауза |
| | ERROR | Грешка |
| **STOPPED** | COMPLETED | Почистване |
| | IDLE | Reset |
| | ERROR | Грешка |
| **COMPLETED** | IDLE | Готов за нова операция |
| | ERROR | Грешка при почистване |
| **ERROR** | IDLE | Възстановяване |
| | INITIALIZING | Пълен reset |
| | ERROR | Остава в грешка |

---

## Контролер на Помпата

### PumpController Класа

Управлява всички операции на помпата с поддръжка на настройки специфични за сегментите.

#### Инициализация

```python
pump_controller = PumpController(
    use_segment_settings=True,     # Използва настройки специфични за сегмента
    logger_context=logger_context,
    glue_settings=glue_settings   # Глобални настройки като fallback
)
```

#### Основни Методи

##### **pump_on(service, robot_service, glue_type, settings=None)**

Стартира помпата с ramp-up последователност:

```python
# Използва настройки на сегмента ако са налични
result = pump_controller.pump_on(
    service=glue_service,
    robot_service=robot_service,
    glue_type=glue_type_address,
    settings=current_segment_settings  # или None за глобални
)
```

**Параметри на Ramp-Up:**
- `motor_speed` - Целева скорост на помпата (RPM или единици)
- `initial_ramp_speed` - Начална скорост за мек старт
- `initial_ramp_speed_duration` - Колко дълго да се поддържа начална скорост
- `forward_ramp_steps` - Брой стъпки за достигане на пълна скорост

##### **pump_off(service, robot_service, glue_type, settings=None)**

Спира помпата с обратна последователност:

```python
pump_controller.pump_off(
    service=glue_service,
    robot_service=robot_service,
    glue_type=glue_type_address,
    settings=current_segment_settings
)
```

**Параметри на Обратната Последователност:**
- `speed_reverse` - Скорост за обратно движение (за предотвратяване на капене)
- `reverse_time` - Продължителност на обратното движение
- `reverse_ramp_steps` - Стъпки за ramp-down

### Режими на Настройки

#### Глобални Настройки (use_segment_settings=False)

```python
# Използва GlueSettings за всички пътища
pump_controller.pump_on(service, robot_service, glue_type, settings=None)
# Скорост от glue_settings.get_motor_speed()
```

#### Настройки Специфични за Сегмента (use_segment_settings=True)

```python
# Използва настройки специфични за пътя
segment_settings = {
    GlueSettingKey.MOTOR_SPEED.value: 12000,
    GlueSettingKey.FORWARD_RAMP_STEPS.value: 3,
    GlueSettingKey.INITIAL_RAMP_SPEED.value: 6000,
    GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: 1.5
}
pump_controller.pump_on(service, robot_service, glue_type, settings=segment_settings)
```

---

## Ръководство за Употреба

### Основна Употреба

#### 1. Инициализация

```python
from glue_dispensing_operation import GlueDispensingOperation

operation = GlueDispensingOperation(
    robot_service=robot_service,
    glue_service=glue_service,
    glue_application=glue_app  # Опционално
)
```

#### 2. Стартиране на Операция

```python
# Дефинирай пътища
paths = [
    {
        'points': [(x1, y1, z1), (x2, y2, z2), ...],
        'settings': {
            'motor_speed': 12000,
            'forward_ramp_steps': 3,
            ...
        }
    },
    # Още пътища...
]

# Стартирай нанасянето
result = operation.start(
    paths=paths,
    spray_on=True  # Активирай пръскането на лепило
)
```

#### 3. Контрол по Време на Изпълнение

```python
# Пауза на операцията
operation.pause()

# Възобновяване на операцията
operation.resume()

# Спиране на операцията
operation.stop()
```

### Усъвършенствана Употреба

#### Персонализирани Обработчици на Състояния

```python
def custom_starting_handler(context: ExecutionContext):
    # Персонализирана логика при стартиране
    context.custom_data = some_value
    return GlueProcessState.MOVING_TO_FIRST_POINT

# Регистрирай персонализиран обработчик
operation.glue_process_state_machine.registry.register_state(
    State(
        state=GlueProcessState.STARTING,
        handler=custom_starting_handler
    )
)
```

#### Мониторинг на Състоянието

```python
# Абонирай се за промени на състоянието
from communication_layer.api.v1.topics import GlueTopics

MessageBroker().subscribe(
    GlueTopics.PROCESS_STATE,
    lambda state: print(f"State changed to: {state}")
)
```

#### Debugging

```python
# Активирай context debugging
ENABLE_CONTEXT_DEBUG = True

# Debug файлове се записват в debug/
# Формат: {timestamp}_{state_name}_ENTER.json
# Формат: {timestamp}_{state_name}_EXIT.json
```

---

## Конфигурация

### Глобална Конфигурация

```python
# В glue_dispensing_operation.py

# Настройки на процеса
USE_SEGMENT_SETTINGS = True              # Използва настройки специфични за сегмента
TURN_OFF_PUMP_BETWEEN_PATHS = True       # Изключва помпата между пътищата
ADJUST_PUMP_SPEED_WHILE_SPRAY = True     # Динамична регулация на скоростта

# Конфигурация на логването
ENABLE_GLUE_DISPENSING_LOGGING = True    # Активира логване

# Конфигурация на debugging
ENABLE_CONTEXT_DEBUG = True              # Записва context snapshots
DEBUG_DIR = "debug/"                     # Директория за debug файлове
```

### Конфигурация на Пътя

Всеки път може да има свои собствени настройки:

```python
path = {
    'points': [...],  # Списък от координати
    'settings': {
        # Настройки на помпата
        GlueSettingKey.MOTOR_SPEED.value: 12000,
        GlueSettingKey.INITIAL_RAMP_SPEED.value: 6000,
        GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: 1.5,
        GlueSettingKey.FORWARD_RAMP_STEPS.value: 3,
        
        # Настройки на обратното движение
        GlueSettingKey.SPEED_REVERSE.value: 2000,
        GlueSettingKey.STEPS_REVERSE.value: 1,
        GlueSettingKey.REVERSE_RAMP_STEPS.value: 2,
        
        # Настройки на робота (ако е приложимо)
        'robot_speed': 50,
        'acceleration': 100
    }
}
```

---

## Обработка на Грешки

### Видове Грешки

#### 1. Грешки при Движение на Робота

```python
try:
    robot_service.move_to_point(point)
except RobotException as e:
    logger.error(f"Robot movement failed: {e}")
    return GlueProcessState.ERROR
```

**Обработка:**
- Спира помпата
- Преминава към ERROR състояние
- Логва детайли за грешката

#### 2. Грешки на Помпата

```python
result = pump_controller.pump_on(...)
if not result:
    logger.error("Failed to start pump")
    return GlueProcessState.ERROR
```

**Обработка:**
- Опит за спиране на помпата
- Преминава към ERROR състояние
- Съхранява контекст за диагностика

#### 3. Грешки при Нишки

```python
try:
    pump_thread.start()
except Exception as e:
    logger.error(f"Failed to start pump adjustment thread: {e}")
    return GlueProcessState.ERROR
```

**Обработка:**
- Почиства всички активни нишки
- Спира помпата
- Преминава към ERROR състояние

### Стратегии за Възстановяване

#### Автоматично Възстановяване

```python
if context.state_machine.state == GlueProcessState.ERROR:
    if context.error_recoverable:
        # Опит за възстановяване
        context.state_machine.transition(GlueProcessState.IDLE)
```

#### Ръчно Възстановяване

```python
# Потребителят трябва да нулира към IDLE
operation.reset()  # Изчиства грешката и преминава към IDLE
```

---

## Функционалност за Пауза/Възобновяване

### Механизъм за Пауза

#### Задействане на Пауза

```python
def pause_operation(operation, context, logger_context):
    current_state = context.state_machine.state
    
    # Записва състояние преди пауза
    context.paused_from_state = current_state
    
    # Записва прогрес
    context.save_progress(
        context.current_path_index,
        context.current_point_index
    )
    
    # Спира помпата
    if context.motor_started:
        context.pump_controller.pump_off(...)
        context.motor_started = False
    
    # Спира нишката за регулация
    if context.pump_thread and context.pump_thread.is_alive():
        # Сигнализира на нишката да спре
        context.pump_thread_stop_event.set()
        context.pump_thread.join(timeout=2.0)
    
    # Преминава към PAUSED
    context.state_machine.transition(GlueProcessState.PAUSED)
    
    return OperationResult(True, "Operation paused")
```

### Механизъм за Възобновяване

#### Задействане на Възобновяване

```python
def resume_operation(context, logger_context):
    if context.state_machine.state != GlueProcessState.PAUSED:
        return OperationResult(False, "Not in paused state")
    
    # Маркира като възобновяване
    context.is_resuming = True
    
    # Възобновява от записаното състояние
    resume_state = context.paused_from_state or GlueProcessState.STARTING
    
    # Преминава към състояние за възобновяване
    context.state_machine.transition(resume_state)
    
    return OperationResult(True, "Operation resumed")
```

#### Логика за Възобновяване в Обработчиците

```python
def handle_moving_to_first_point_state(context, resume):
    if context.is_resuming:
        # Движи се към запазената позиция
        target_index = context.current_point_index
        
        # Ескалация от запазената позиция
        points_from_saved = context.current_path[target_index:]
        
    else:
        # Нормално изпълнение от началото
        target_index = 0
        points_from_saved = context.current_path
    
    # Движение към целевата точка
    robot_service.move_to_point(points_from_saved[0])
    
    # Изчиства флага за възобновяване
    context.is_resuming = False
    
    return GlueProcessState.EXECUTING_PATH
```

### Записани Данни при Пауза

```python
# ExecutionContext.save_progress()
{
    "paused_from_state": GlueProcessState.SENDING_PATH_POINTS,
    "current_path_index": 2,        # Път #2
    "current_point_index": 145,     # Точка #145
    "target_point_index": 146,      # Робот се движи към #146
    "motor_started": True,
    "spray_on": True
}
```

---

## Отстраняване на Грешки

### Debug Изход

#### Автоматични Debug Файлове

Когато `ENABLE_CONTEXT_DEBUG = True`, системата записва JSON файлове при всяка промяна на състояние:

```json
{
    "timestamp": "20251209_143025_123456",
    "state": "SENDING_PATH_POINTS_ENTER",
    "context": {
        "current_path_index": 1,
        "current_point_index": 42,
        "total_paths": 5,
        "current_path_length": 250,
        "spray_on": true,
        "motor_started": true,
        "current_state": "GlueProcessState.SENDING_PATH_POINTS",
        "pump_thread_alive": true,
        "has_current_settings": true,
        "settings_keys": ["motor_speed", "forward_ramp_steps", ...]
    }
}
```

#### Структура на Debug Файловете

```
debug/
├── 20251209_143020_STARTING_ENTER.json
├── 20251209_143020_STARTING_EXIT.json
├── 20251209_143021_MOVING_TO_FIRST_POINT_ENTER.json
├── 20251209_143021_MOVING_TO_FIRST_POINT_EXIT.json
├── 20251209_143025_EXECUTING_PATH_ENTER.json
...
```

### Логване

#### Структурирано Логване

```python
from modules.utils.custom_logging import (
    log_debug_message,
    log_error_message,
    LoggerContext
)

# Инициализация на logger
logger_context = LoggerContext(
    enabled=ENABLE_GLUE_DISPENSING_LOGGING,
    logger=glue_dispensing_logger
)

# Debug съобщение
log_debug_message(
    logger_context,
    message=f"Starting path {path_index}: {len(points)} points"
)

# Съобщение за грешка
log_error_message(
    logger_context,
    message=f"Failed to send point {point_index}: {error}"
)
```

#### Лог Изход

```
[2025-12-09 14:30:20] [Glue Dispensing] Starting path 1: 250 points
[2025-12-09 14:30:21] [Glue Dispensing] Pump ON (segment): {'motor_speed': 12000, ...}
[2025-12-09 14:30:25] [Glue Dispensing] Sending point 42/250
[2025-12-09 14:30:30] [Glue Dispensing] Path 1 completed
```

### Техники за Отстраняване на Грешки

#### 1. Проследяване на Състоянието

```python
# Мониторинг на преходите между състоянията
def on_state_change(new_state):
    print(f"State: {new_state}")
    print(f"Path: {context.current_path_index}/{len(context.paths)}")
    print(f"Point: {context.current_point_index}")

MessageBroker().subscribe(GlueTopics.PROCESS_STATE, on_state_change)
```

#### 2. Анализ на Context Snapshots

```python
import json

# Зареди debug файл
with open('debug/20251209_143025_SENDING_PATH_POINTS_ENTER.json') as f:
    debug_data = json.load(f)

# Анализирай контекста
ctx = debug_data['context']
print(f"Was at path {ctx['current_path_index']}, point {ctx['current_point_index']}")
print(f"Pump running: {ctx['motor_started']}")
print(f"Thread alive: {ctx['pump_thread_alive']}")
```

#### 3. Проверка на Състоянието на Помпата

```python
# Добави логване в PumpController
def pump_on(self, ...):
    log_debug_message(
        self.logger_context,
        message=f"Pump ON: speed={speed}, ramp_steps={ramp_steps}"
    )
    result = service.motorOn(...)
    log_debug_message(
        self.logger_context,
        message=f"Pump ON result: {result}"
    )
    return result
```

#### 4. Мониторинг на Нишки

```python
# Проверка на състоянието на нишката
if context.pump_thread:
    print(f"Pump thread alive: {context.pump_thread.is_alive()}")
    print(f"Pump ready event set: {context.pump_ready_event.is_set()}")
```

---

## Често Задавани Въпроси

### Въпроси за Общо Използване

**В: Как да стартирам операция без пръскане на лепило (dry run)?**

```python
result = operation.start(paths=paths, spray_on=False)
```

**В: Как да използвам глобални настройки вместо настройки на сегменти?**

```python
# В glue_dispensing_operation.py
USE_SEGMENT_SETTINGS = False
```

**В: Може ли да паузирам операцията и да продължа по-късно?**

Да:
```python
operation.pause()
# ... някакво време по-късно ...
operation.resume()  # Продължава от запазената позиция
```

### Въпроси за Отстраняване на Проблеми

**В: Операцията остава в ERROR състояние. Как да възстановя?**

```python
# Ръчен reset към IDLE
operation.reset()
# или
operation.execution_context.state_machine.transition(GlueProcessState.IDLE)
```

**В: Помпата не спира между пътищата.**

```python
# Провери конфигурацията
TURN_OFF_PUMP_BETWEEN_PATHS = True  # Трябва да е True
```

**В: Динамичната регулация на скоростта не работи.**

```python
# Провери конфигурацията
ADJUST_PUMP_SPEED_WHILE_SPRAY = True

# Провери дали нишката стартира
if context.pump_thread and context.pump_thread.is_alive():
    print("Adjustment thread is running")
```

**В: Debug файловете не се генерират.**

```python
# Активирай context debugging
ENABLE_CONTEXT_DEBUG = True

# Провери дали debug/ директорията е създадена
import os
os.makedirs(DEBUG_DIR, exist_ok=True)
```

### Въпроси за Производителност

**В: Как да оптимизирам скоростта на изпълнение?**

- Намали логването: `ENABLE_GLUE_DISPENSING_LOGGING = False`
- Деактивирай context debugging: `ENABLE_CONTEXT_DEBUG = False`
- Използвай по-малко ramp steps в настройките на помпата
- Увеличи robot speed в настройките на пътя

**В: Колко бързо може да се изпълни един път?**

Зависи от:
- Брой точки в пътя
- Скорост на робота
- Ramp-up време на помпата
- Мрежова латентност към робота

---

## Заключение

Модулът за Процес на Нанасяне на Лепило осигурява **надежден, възобновяем и наблюдаем** процес за изпълнение на операции по нанасяне на лепило. Използвайки изпълнима машина на състоянията, той гарантира:

- ✅ **Предвидимо поведение** чрез ясни дефиниции на състояния и преходи
- ✅ **Възстановяемост** чрез функционалност за пауза/възобновяване
- ✅ **Наблюдаемост** чрез структурирано логване и debug изход
- ✅ **Гъвкавост** чрез настройки специфични за сегментите
- ✅ **Разширяемост** чрез персонализирани обработчици на състояния
- ✅ **Сигурност** чрез валидирани правила за преход

За технически въпроси или допълнения, вижте кода на модула или се свържете с екипа за разработка.

---

**Край на Документацията**

