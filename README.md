# Эмулятор командной оболочки UNIX (вариант 10)

Практическая работа по дисциплине «Конфигурационное управление».

## Общее описание

Эмулятор командной строки UNIX-подобной ОС с графическим интерфейсом
(Python + tkinter). Окно выглядит как терминал: в области вывода
отображаются введённые команды и их результат, ошибки выделяются
красным, внизу находится строка ввода с приглашением.

Выполненные этапы:

1. **REPL** — окно, парсер с переменными окружения, заглушки `ls`/`cd`,
   `exit`.
2. **Конфигурация** — параметры командной строки, журнал вызовов
   команд в CSV, стартовый скрипт.
3. **VFS** — виртуальная файловая система из папки на диске, работа
   в памяти, служебная команда `vfs-info`.
4. **Основные команды** — настоящие `ls` и `cd`, новые команды `rev`,
   `date`, `tac`.
5. **Дополнительные команды** — `rm` и `rmdir`, изменяющие VFS только
   в памяти.

## Структура репозитория

```
src/
  main.py               точка входа
  emulator/
    config.py           параметры командной строки
    parser.py           разбор строки и подстановка переменных окружения
    commands/           реализация команд
      base.py           результат, ошибки, разбор опций, доступ к VFS
      navigation.py     ls, cd
      text.py           rev, tac
      modify.py         rm, rmdir
      system.py         exit, date, vfs-info
    shell.py            ядро: выполнение строки, приглашение, журнал
    logger.py           журнал вызовов команд (CSV)
    script.py           чтение и выполнение стартового скрипта
    vfs.py              VFS в памяти: загрузка из папки, хеш SHA-256
    gui.py              графический интерфейс (tkinter)
tests/                  модульные тесты (unittest)
examples/
  vfs/                  примеры VFS: minimal, several, deep
  startup/              стартовые скрипты эмулятора
  test_*.bat, test_*.sh скрипты ОС для проверки эмулятора
run.bat, run.sh         запуск эмулятора и тестов
```

## Функции и настройки

### Параметры командной строки

| Параметр        | Описание                                              |
|-----------------|-------------------------------------------------------|
| `--vfs PATH`    | путь к физическому расположению VFS; имя VFS — последняя часть пути |
| `--log FILE`    | путь к лог-файлу CSV (папки создаются автоматически)  |
| `--script FILE` | путь к стартовому скрипту                             |
| `-h`, `--help`  | справка по параметрам                                 |

Все параметры необязательны. При запуске эмулятор печатает отладочный
вывод со значениями всех параметров (в консоль и в окно):

```
[debug] vfs path     = examples/vfs/deep
[debug] vfs name     = deep
[debug] log file     = logs/session.csv
[debug] start script = (not set)
```

Неизвестный параметр или параметр без значения — ошибка: эмулятор
не запускается, код завершения 2. Если лог-файл нельзя открыть или
VFS не удалось загрузить, ошибка выводится красным в окне (и в
консоль), а эмулятор продолжает работу без журнала / без VFS.

### Виртуальная файловая система (VFS)

Источник VFS — папка на диске пользователя (`--vfs PATH`). При
запуске вся папка — структура и содержимое файлов (включая двоичные)
— читается в память. Дальше все операции выполняются только с копией
в памяти: данные на диске никогда не изменяются. Символические ссылки
и специальные файлы пропускаются.

Ошибки загрузки: папка не существует, путь указывает на файл, нет
прав на чтение.

**Хеш SHA-256** вычисляется по данным VFS в памяти. Узлы обходятся
в порядке сортировки имён; для каждой папки хешируется
`D <путь>\0`, для каждого файла — `F <путь>\0<размер>\0<содержимое>`
(пути от корня VFS вида `/home/user`, UTF-8). Поэтому хеш меняется
при изменении содержимого, имени или расположения любого файла и
не зависит от того, где папка VFS лежит на диске.

Примеры VFS в `examples/vfs/` (git хранит их байт-в-байт, без
преобразования переводов строк, чтобы хеш совпадал на любой ОС):

| VFS       | Содержимое                                              |
|-----------|---------------------------------------------------------|
| `minimal` | один файл                                               |
| `several` | несколько файлов в корне                                |
| `deep`    | 4 уровня папок, имена с пробелом и кириллицей           |

### Журнал (CSV)

Каждый вызов команды (в том числе ошибочный) — одна строка журнала.
Файл дописывается, заголовок пишется только в новый файл.

| Столбец     | Содержимое                                       |
|-------------|--------------------------------------------------|
| `date`      | дата события, `ГГГГ-ММ-ДД`                       |
| `time`      | время события, `ЧЧ:ММ:СС`                        |
| `command`   | имя команды (пусто при ошибке разбора)           |
| `arguments` | аргументы после подстановки переменных           |
| `status`    | `ok` или `error`                                 |
| `error`     | сообщение о возникшей ошибке                     |

### Стартовый скрипт

Текстовый файл в UTF-8, одна команда в строке. Пустые строки и
комментарии `# ...` пропускаются. Каждая команда показывается в окне
вместе с приглашением и выводом, как если бы её ввёл пользователь.
**Выполнение останавливается на первой ошибке** — в окне появляется
`--- script stopped: error at line N ---`, после чего можно продолжать
работу вручную. Команда `exit` в скрипте закрывает эмулятор.

### Графический интерфейс

* Заголовок окна содержит имя VFS: `Shell Emulator — deep`.
* Приглашение к вводу: `<имя VFS>:<текущий каталог>$ `.
* `Enter` — выполнить команду, `↑`/`↓` — листать историю ввода.
* Цвета: обычный вывод, ошибки (красный), отладочный вывод (серый).

### Парсер командной строки

| Синтаксис          | Значение                                            |
|--------------------|-----------------------------------------------------|
| `$NAME`, `${NAME}` | значение переменной окружения реальной ОС           |
| `'...'`            | текст как есть, переменные не раскрываются          |
| `"..."`            | переменные раскрываются, пробелы сохраняются        |
| `\x`               | символ `x` берётся буквально (`\$`, `\ `, `\"`)     |
| `# ...`            | комментарий до конца строки (в начале слова)        |

Неизвестная переменная заменяется пустой строкой. Ошибки разбора:
незакрытая кавычка, `\` в конце строки, некорректная подстановка
`${...}`.

### Команды

| Команда                   | Описание                                      |
|---------------------------|-----------------------------------------------|
| `ls [-a] [-l] [путь...]`  | содержимое папок или сведения о файлах        |
| `cd [путь \| -]`          | сменить текущую папку                         |
| `rev файл...`             | строки файлов с символами в обратном порядке  |
| `tac файл...`             | строки каждого файла в обратном порядке       |
| `date [-u] [+ФОРМАТ]`     | текущие дата и время                          |
| `rm [-rRfdv] путь...`     | удалить файлы и папки (только в памяти)       |
| `rmdir [-pv] папка...`    | удалить пустые папки (только в памяти)        |
| `exit [N]`                | закрыть эмулятор с кодом `N` (по умолчанию 0) |
| `vfs-info`                | служебная: имя VFS, путь-источник, хеш SHA-256, число папок и файлов, размер |

Общие правила, как в UNIX:

* пути абсолютные (`/etc/hostname`) или относительные текущей папки
  (`docs/a.txt`), поддерживаются `.` и `..`;
* опции можно объединять (`-la`) и ставить в любом месте; после `--`
  аргументы опциями не считаются; неизвестная опция —
  `invalid option -- 'x'`;
* если один из нескольких путей ошибочен, остальные всё равно
  обрабатываются, а ошибка выводится отдельно;
* команды, работающие с VFS, без загруженной VFS выводят
  `no VFS loaded`; неизвестная команда — `<имя>: command not found`.

**`ls`**. Без аргументов — текущая папка. Имена сортируются; имена
с пробелами берутся в кавычки (`'my docs'`). Скрытые файлы (имя
начинается с точки) показываются только с `-a`, вместе с `.` и `..`.
`-l` — подробный формат: тип и права (`drwxr-xr-x` для папок,
`-rw-r--r--` для файлов — VFS не хранит права), размер в байтах
(для папок 4096), имя. Для нескольких путей перед содержимым каждой
папки выводится заголовок `путь:`. Ошибки: `cannot access 'x': No
such file or directory`.

**`cd`**. Без аргументов — переход в корень VFS `/`. `cd -` —
переход в предыдущую папку (новый путь выводится, как в bash).
Текущая папка показывается в приглашении. Ошибки: `No such file or
directory`, `Not a directory` (путь к файлу), `too many arguments`.
При ошибке текущая папка не меняется.

**`rev`, `tac`**. Файлы читаются из VFS как текст UTF-8. Стандартного
ввода в эмуляторе нет, поэтому нужен хотя бы один файл. Ошибки:
`missing file operand`, `No such file or directory`, `Is a directory`.

**`date`**. Без аргументов — формат GNU date: `Tue Oct  6 19:25:55
MSK 2026` (если у часового пояса нет короткого имени, как в Windows,
выводится смещение `+0300`). `-u` — время UTC. `+ФОРМАТ` — свой
формат с кодами strftime: `date +%Y-%m-%d`, `date "+%H:%M:%S"`.
Ошибки: `invalid date 'x'` (аргумент без `+`), `extra operand`.

**`rm`, `rmdir`** изменяют только VFS в памяти: папка на диске
остаётся прежней, а хеш в `vfs-info` после удаления меняется.

`rm` удаляет файлы. Опции: `-r`/`-R` — папки со всем содержимым,
`-d` — пустые папки, `-f` — молча пропускать несуществующие пути
(и не требовать аргументов), `-v` — выводить каждый удалённый файл и
папку (`removed 'x'`, `removed directory 'x'`). Ошибки: `missing
operand`, `cannot remove 'x': No such file or directory`, `Is a
directory` (папка без `-r`/`-d`), `Directory not empty` (`-d` для
непустой папки), `it is dangerous to operate recursively on '/'`
(`rm -r /`), `refusing to remove '.' or '..' directory`,
`Device or resource busy` (текущая папка или папка, в которой она
лежит).

`rmdir` удаляет пустые папки. Опции: `-p` — также удалить
родительские папки из пути, если они стали пустыми (`rmdir -p a/b/c`
удаляет `a/b/c`, `a/b`, `a`; останавливается на первой непустой),
`-v` — выводить каждую удалённую папку. Ошибки: `missing operand`,
`failed to remove 'x': Directory not empty`, `Not a directory`,
`No such file or directory`, `Invalid argument` (`.` и `..`),
`Device or resource busy` (текущая папка и корень).

## Запуск и тесты

Требуется Python 3.8+ с модулем tkinter (входит в стандартную
установку Python для Windows). Сборка не требуется.

Windows:

```bat
run.bat                                   :: запуск эмулятора
run.bat --vfs my_vfs --log logs\log.csv --script start.txt
run.bat test                              :: запуск тестов
```

Linux / macOS:

```sh
./run.sh                                  # запуск эмулятора
./run.sh --vfs my_vfs --log logs/log.csv --script start.txt
./run.sh test                             # запуск тестов
```

Тесты вручную: `PYTHONPATH=src python -m unittest discover -s tests -v`.

### Скрипты проверки

| Скрипт (`.bat` / `.sh`)    | Что проверяет                                   |
|----------------------------|-------------------------------------------------|
| `examples/test_params`     | запуск без параметров, только `--vfs`, все три параметра + вывод журнала |
| `examples/test_script`     | скрипт с `exit 3`, остановка на ошибке, отсутствующий скрипт |
| `examples/test_errors`     | `--help`, неизвестный параметр, параметр без значения, недоступный лог-файл |
| `examples/test_vfs`        | VFS `minimal`, `several`, `deep`; на `deep` — все команды этапов 1–3 |
| `examples/test_vfs_errors` | несуществующая папка VFS, файл вместо папки, запуск без `--vfs` |
| `examples/test_commands`   | все режимы команд этапа 4 (`stage4.txt`), затем каждый сценарий ошибки из `startup/errors/` |
| `examples/test_modify`     | все режимы `rm` и `rmdir` (`stage5.txt`), сценарии ошибок `startup/errors/rm*.txt`, затем список файлов VFS на диске — они не изменились |

Стартовые скрипты в `examples/startup/`:

| Скрипт         | Назначение                                             |
|----------------|--------------------------------------------------------|
| `demo.txt`     | несколько команд без ошибок                            |
| `error.txt`    | остановка на ошибке в строке 4                         |
| `exit.txt`     | завершение эмулятора командой `exit 3`                 |
| `vfs_info.txt` | вывод `vfs-info`                                       |
| `stage3.txt`   | команды этапов 1–3                                     |
| `stage4.txt`   | все режимы `ls`, `cd`, `rev`, `tac`, `date`            |
| `stage5.txt`   | все режимы `rm` и `rmdir`, хеш VFS до и после изменений |
| `errors/*.txt` | по одной ошибке в каждом: `ls`, `cd`, `rev`, `tac`, `date`, `rm`, `rmdir` |

Так как стартовый скрипт останавливается на первой ошибке, в каждом
скрипте ошибочная команда стоит последней, а разные ошибки разнесены
по отдельным скриптам в `errors/`. Скрипты рассчитаны на запуск с
`--vfs examples/vfs/deep`.

Каждый запуск открывает окно эмулятора; чтобы перейти к следующей
проверке, закройте окно или введите `exit`. Журналы пишутся в
`examples/logs/` (папка не хранится в репозитории).

## Примеры использования

Работа с VFS (`run.bat --vfs examples\vfs\deep`):

```
deep:/$ ls
etc  home  readme.txt  var
deep:/$ ls -la home/user
drwxr-xr-x     4096 .
drwxr-xr-x     4096 ..
-rw-r--r--       43 .profile
drwxr-xr-x     4096 docs
drwxr-xr-x     4096 'my docs'
deep:/$ ls /etc /var/log
/etc:
app  hostname

/var/log:
system.log
deep:/$ cd home/user/docs/drafts
deep:/home/user/docs/drafts$ cd ../..
deep:/home/user$ cd "my docs"    # комментарий
deep:/home/user/my docs$ cd -
/home/user
deep:/home/user$ cd
deep:/$ rev /etc/hostname
tsoh-rotalume
deep:/$ tac /var/log/system.log
2026-10-01 10:01:00 user logged in
2026-10-01 10:00:05 network up
2026-10-01 10:00:00 system started
deep:/$ date
Tue Oct  6 19:25:55 +0300 2026
deep:/$ date +%d.%m.%Y
06.10.2026
```

Ошибки:

```
deep:/$ ls /nope readme.txt
readme.txt
ls: cannot access '/nope': No such file or directory
deep:/$ ls -z
ls: invalid option -- 'z'
deep:/$ cd /etc/hostname
cd: /etc/hostname: Not a directory
deep:/$ cd a b
cd: too many arguments
deep:/$ rev /etc
rev: /etc: Is a directory
deep:/$ tac
tac: missing file operand
deep:/$ date tomorrow
date: invalid date 'tomorrow'
deep:/$ foo
foo: command not found
deep:/$ ls 'abc
parse error: unexpected end of line: unclosed single quote
deep:/$ exit abc
exit: abc: numeric argument required
deep:/$ exit
```

Переменные окружения реальной ОС раскрываются парсером, например
`date "+%H:%M $USERNAME"` в Windows или `date "+%H:%M $USER"` в Linux.
Неизвестная переменная заменяется пустой строкой:
`ls "$NO_SUCH_VAR/etc"` выводит содержимое `/etc`.

Информация о VFS (`run.bat --vfs examples\vfs\deep`):

```
deep:/$ vfs-info
name:    deep
source:  C:\...\examples\vfs\deep
sha256:  fd3ce12cecf09a40107086738fd6f6073efd57a07ca2cb88a39eeb97011c4eae
content: 9 directories, 8 files, 448 bytes
deep:/$ vfs-info --verbose
vfs-info: too many arguments
```

Изменение VFS в памяти (`rm`, `rmdir`):

```
deep:/$ rm -v readme.txt /etc/hostname
removed 'readme.txt'
removed '/etc/hostname'
deep:/$ rm /var/log/system.log
deep:/$ rmdir -pv var/log
rmdir: removing directory, 'var/log'
rmdir: removing directory, 'var'
deep:/$ rm -rv /home/user/docs
removed '/home/user/docs/drafts/plan.txt'
removed directory '/home/user/docs/drafts'
removed '/home/user/docs/report.txt'
removed directory '/home/user/docs'
deep:/$ ls -a /
.  ..  etc  home
deep:/$ rm /etc
rm: cannot remove '/etc': Is a directory
deep:/$ rmdir /etc
rmdir: failed to remove '/etc': Directory not empty
deep:/$ cd /home/user
deep:/home/user$ rm -r /home
rm: cannot remove '/home': Device or resource busy
deep:/home/user$ rm -r /
rm: it is dangerous to operate recursively on '/'
```

После выхода из эмулятора все файлы в `examples/vfs/deep` на диске
остаются на месте.

Ошибка загрузки VFS (`--vfs examples\vfs\no_such_vfs`):

```
cannot load VFS: 'examples\vfs\no_such_vfs': no such directory
no_such_vfs:/$ vfs-info
vfs-info: no VFS loaded (use --vfs PATH)
```

Стартовый скрипт с ошибкой (`examples/startup/error.txt`):

```
--- startup script: examples/startup/error.txt ---
deep:/$ ls -a
.  ..  etc  home  readme.txt  var
deep:/$ cd /home
deep:/home$ cd too many
cd: too many arguments
--- script stopped: error at line 4 ---
```

Журнал после этого скрипта:

```
date,time,command,arguments,status,error
2026-10-06,19:30:12,ls,-a,ok,
2026-10-06,19:30:12,cd,/home,ok,
2026-10-06,19:30:12,cd,too many,error,cd: too many arguments
```
