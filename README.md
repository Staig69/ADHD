```mermaid
classDiagram
    class App {
        -ui: QUiLoader
        -engine: ADHD_Backend
        -timer_logic: Timer
        -current_task_index: int
        -time_left: int
        -is_break: bool
        +setup_ui_elements()
        +setup_connections()
        +show_time_hint()
        +generate_tasks()
        +clear_tasks_layout()
        +start_focus_session()
        +hidden_timer_tick()
        +update_status_ui()
        +stop_focus_session()
        +finish_app()
    }

    class ADHD_Backend {
        -is_blocking: bool
        -subtasks_list: list
        -original_task: str
        +start_blocking()
        +stop_blocking()
        +generate_initial_plan(task_text, work_mins)
    }

    class Timer {
        -work_duration: int
        -break_duration: int
        +set_durations(work_mins, break_mins)
    }

    class taskSplitter {
        <<module>>
        +split_tasks(task_description: str, time_minutes: int, tasks_performed: str)
    }

    class sites_block {
        <<module>>
        +redirect_browser()
    }

    class process_block {
        <<module>>
        +kill_apps()
    }

    class config {
        <<utility>>
        +BLOCK_APPS: list
        +BLOCK_SITES: list
        +CHEK_INTERVAL: int
        +BASE_DIR: str
        +HTML_FILE_PATH: str
        +REDIRECT_URL: str
    }

    App *-- ADHD_Backend : получает указания
    App *-- Timer : управляет временем
    
    ADHD_Backend ..> taskSplitter : вызывает разделение задач
    ADHD_Backend ..> process_block : закрывает процессы
    ADHD_Backend ..> sites_block : блокирует сайты
    
    process_block ..> config : читает список процессов
    sites_block ..> config : читает URL и сайты