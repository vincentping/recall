# 用户端设计方案

> **创建日期:** 2026-02-14
> **状态:** 已实现
> **范围:** 面向学习者的练习、答题、成绩追踪功能

---

## 一、架构

### 1.1 目录结构

```
src/ui/
├── main_window.py              # 程序外壳（菜单栏、主题、语言、窗口管理）
├── home_page.py                # 首页（学习统计 + 练习启动）
├── practice_window.py          # 答题界面（学习模式 + 考试模拟）
├── practice_result.py          # 练习结果页
└── admin/                      # 管理端（通过菜单栏进入）
    ├── input_window.py
    ├── batch_import_window.py
    ├── question_manager_window.py
    └── exam_manager.py
```

### 1.2 MainWindow 结构

- 中央部件为 `QStackedWidget`，包含三个页面
- 管理端窗口通过 Admin 菜单打开（独立窗口，按需创建）

**页面切换流程:**
```
MainWindow (QStackedWidget)
├── Page 0: HomePage          ← 启动默认
├── Page 1: PracticeWindow    ← 点击"开始练习"切换
└── Page 2: PracticeResult    ← 练习完成后切换
```

**信号流:**
```
HomePage  --start_practice(config)--> MainWindow --> PracticeWindow
PracticeWindow --practice_finished(result)--> MainWindow --> PracticeResult
PracticeWindow --practice_cancelled()--> MainWindow --> HomePage
PracticeResult --back_home()--> MainWindow --> HomePage
PracticeResult --start_new()--> MainWindow --> HomePage
PracticeResult --retry_wrong(question_ids)--> MainWindow --> PracticeWindow
```

### 1.3 菜单栏

```
File        Language    View              Admin                Help
├─ Exit     ├─ English  ├─ Theme ►        ├─ Exam Manager      ├─ About
            ├─ Chinese  └─ Font Size ►    ├─ New Question Entry
                                          ├─ Batch Import from Markdown
                                          ├─ Manage Questions (Edit/Delete)
                                          └─ Reset Statistics
```

---

## 二、数据库

### 2.1 练习相关表

```sql
CREATE TABLE IF NOT EXISTS Practice_Sessions (
    session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id     INTEGER,
    mode          TEXT NOT NULL DEFAULT 'learn',     -- 'learn' 或 'exam'
    total_count   INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    duration_sec  INTEGER DEFAULT 0,
    started_at    TEXT NOT NULL,                     -- ISO 8601
    finished_at   TEXT,
    FOREIGN KEY (module_id) REFERENCES Knowledge_Modules(module_id)
);

CREATE TABLE IF NOT EXISTS Answer_Records (
    record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL,
    question_id   INTEGER NOT NULL,
    user_answer   TEXT,                             -- 如 "B" 或 "A,C"
    is_correct    INTEGER NOT NULL DEFAULT 0,
    time_spent    INTEGER DEFAULT 0,               -- 秒
    answered_at   TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES Practice_Sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
);
```

### 2.2 DBManager 方法

```python
# 练习记录
def create_practice_session(self, module_id, mode, total_count) -> int
def finish_practice_session(self, session_id, correct_count, duration_sec)
def save_answer_record(self, session_id, question_id, user_answer, is_correct, time_spent)

# 统计查询
def get_total_practiced_count(self) -> int
def get_overall_accuracy(self) -> float
def get_recent_sessions(self, limit=5) -> list[dict]
def get_module_accuracy(self) -> list[dict]
def get_wrong_question_ids(self, module_id=None, chapter_numbers=None, limit=50) -> list[int]
def get_today_stats(self) -> dict
def get_random_question_ids(self, module_id, chapter_numbers, count, flagged_only) -> list[int]
def reset_practice_stats(self) -> bool
```

---

## 三、首页 HomePage

### 3.1 布局

```
┌──────────────────────────────────────────────────────┐
│  【简要统计区】（可展开/收起）                          │
│  已练习: 320 题    正确率: 82%    最近得分: 85%       │
│  [▼ 查看详情]                                        │
│                                                      │
│  展开后:                                             │
│  各模块掌握度（进度条 + 百分比 + 练习次数）             │
│  薄弱环节提示（正确率 < 60% 的模块）                   │
│                                                      │
│  ──────────────────────────────────────────────────  │
│                                                      │
│  【练习设置区】                                       │
│  练习模式:  ● 学习模式  ○ 考试模拟                    │
│  模块: [Core 1 ▼]       章节: [全部章节 ▼]           │
│  题数: [20 ▼]                                        │
│  ☐ 仅标记的题目  ☐ 仅答错过的题目                     │
│  时间限制: [90] 分钟  （仅考试模式可见）               │
│                                                      │
│              [ 开始练习 ]                             │
└──────────────────────────────────────────────────────┘
```

### 3.2 组件说明

**统计区:**
- 收起：一行 3 个数字（总练习数、正确率、最近得分）
- 展开：`QProgressBar` 显示各模块掌握度 + 薄弱环节提醒
- 无记录时显示"还没有练习记录，开始第一次练习吧！"
- 隐藏 `_default` 模块（无模块考试的内部模块）

**练习设置区:**
- `QRadioButton`：学习模式 / 考试模拟
- `QComboBox`：模块筛选（单模块考试时自动隐藏）、章节筛选
- `QSpinBox`：题数（1-500，默认 20）、考试时间（1-300 分钟，默认 90）
- `QCheckBox`：仅标记 / 仅错题

**start_practice 信号数据:**
```python
config = {
    'mode': 'learn' | 'exam',
    'module_id': int | None,
    'module_name': str,
    'chapter_numbers': list[str] | None,
    'count': int,
    'flagged_only': bool,
    'wrong_only': bool,
    'time_limit_min': int,  # 仅考试模式
}
```

---

## 四、答题界面 PracticeWindow

### 4.1 布局

```
┌──────────────────────────────────────────────────────┐
│  【顶部】                                             │
│  题目: 5 / 20    学习模式    [剩余时间: 85:30]       │
│                                                      │
│  【题目区域】（QTextEdit 只读）                        │
│  Which of the following is the default port for HTTP? │
│  (Multiple Choice - select one)                       │
│                                                      │
│  【选项区域】（QScrollArea）                           │
│  ○  A. 21                                            │
│  ●  B. 80                                            │
│  ○  C. 443                                           │
│  ○  D. 8080                                          │
│                                                      │
│  【解析区域】（检查后显示，仅学习模式）                  │
│  ✓ 正确！                                             │
│  HTTP 的默认端口是 80。HTTPS 使用 443。                │
│                                                      │
│  【底部】                                             │
│  [标记]  [检查]  [取消]  [上一题]  [下一题]  [提交]   │
└──────────────────────────────────────────────────────┘
```

### 4.2 学习模式

1. 显示题目和选项（答案已随机打乱，缓存顺序）
2. 用户选择答案后点**"检查"** → 正确选项标绿、错选标红、选项锁定、显示解析
3. 可点"下一题"跳过不检查
4. 自由前后跳转：未检查的题可修改，已检查的题只读
5. 点"提交"结束练习（提示未作答题数）

### 4.3 考试模式

1. 无"检查"按钮，有"标记"按钮（练习内临时标记，不保存到 DB）
2. 倒计时 `QTimer`，剩余 5 分钟变警告色，1 分钟变危险色
3. 时间到自动提交
4. 任何时候都可修改答案和前后跳转
5. 提交时显示未作答/已标记数量的确认对话框

### 4.4 内部状态

```python
self.question_ids: list[int]           # 题目ID队列
self.current_index: int                # 当前索引
self.user_answers: dict[int, str]      # {q_id: "B" or "A,C"}
self.checked_set: set[int]             # 已检查的题目（学习模式）
self.results: dict[int, bool]          # {q_id: is_correct}
self.time_per_question: dict[int, int] # {q_id: seconds}
self.practice_marks: set[int]          # 临时标记
self.question_cache: dict[int, dict]   # 缓存题目数据
self.option_order_cache: dict[int, list] # 缓存打乱后的选项顺序
self.session_id: int                   # DB 会话 ID
```

### 4.5 答案正确性判定

使用打乱后的选项顺序（`option_order_cache`）确定每个选项的 A/B/C/D 标签，然后比较用户选择与正确标签是否一致。

---

## 五、练习结果页 PracticeResult

### 5.1 布局

```
┌──────────────────────────────────────────────────────┐
│  【成绩概览】                                         │
│  得分: 17 / 20 (85%)                                 │
│  ████████████████████░░░░  85%                       │
│  用时: 12 分 35 秒    平均每题: 38 秒                  │
│  (考试模式: 及格线 675/900 (75%)  结果: 通过 ✓)       │
│                                                      │
│  ──────────────────────────────────────────────────  │
│                                                      │
│  【题目回顾】（全部题目，滚动列表）                     │
│  Q1. 正确  题干...                                    │
│      A. xxx  B. xxx [你的答案] [正确答案]  C. xxx     │
│      [展开解析 ▼]                                     │
│  Q2. 错误  题干...                                    │
│      A. xxx  B. xxx [你的答案, 划线]  C. xxx [正确]    │
│      [展开解析 ▼]                                     │
│  ...                                                 │
│                                                      │
│  [重新练习错题]    [开始新练习]    [返回首页]           │
└──────────────────────────────────────────────────────┘
```

### 5.2 数据输入

```python
result_data = {
    'session_id': int,
    'mode': 'learn' | 'exam',
    'total_count': int,
    'correct_count': int,
    'duration_sec': int,
    'module_name': str,
    'questions': [
        {
            'question_id': int,
            'question_text': str,
            'question_type': 'MC' | 'MR',
            'user_answer': str,         # "B" 或 "A,C"
            'correct_answer': str,
            'is_correct': bool,
            'explanation': str,
            'time_spent': int,
            'answers': list[dict],      # 打乱后的选项列表
        }
    ]
}
```

### 5.3 操作按钮

| 按钮 | 信号 | 行为 |
|------|------|------|
| 重新练习错题 | `retry_wrong(list[int])` | 用错题 ID 发起学习模式练习 |
| 开始新练习 | `start_new()` | 返回首页 |
| 返回首页 | `back_home()` | 返回首页 |

---

## 六、主题集成

### 6.1 theme JSON 扩展

`default.json` 和 `dark.json` 均包含 `practice` 节点：

```json
{
  "practice": {
    "correct_bg": "#e6f4ea",
    "correct_border": "#34a853",
    "correct_text": "#137333",
    "incorrect_bg": "#fce8e6",
    "incorrect_border": "#ea4335",
    "incorrect_text": "#c5221f",
    "timer_normal": "#5f6368",
    "timer_warning": "#f9ab00",
    "timer_danger": "#ea4335",
    "progress_high": "#34a853",
    "progress_mid": "#f9ab00",
    "progress_low": "#ea4335"
  }
}
```

### 6.2 QSS 动态样式

通过 `widget.setProperty("result", "correct/incorrect")` 动态设置选项高亮：
```css
QRadioButton[result="correct"], QCheckBox[result="correct"] {
    background-color: ...; border: 2px solid ...;
}
QRadioButton[result="incorrect"], QCheckBox[result="incorrect"] {
    background-color: ...; border: 2px solid ...;
}
```

倒计时通过 `timer_label.setProperty("timer", "warning/danger")` 切换颜色。

---

## 七、国际化

### 7.1 翻译上下文

| 文件 | 上下文名 |
|------|---------|
| `home_page.py` | `"HomePage"` |
| `practice_window.py` | `"PracticeWindow"` |
| `practice_result.py` | `"PracticeResult"` |
| `exam_manager.py` | `"ExamManager"` |

所有文件使用 `self.tr()` → `QCoreApplication.translate(context, text)`。

### 7.2 语言切换

`MainWindow.change_language()` 调用所有活动页面和打开的管理窗口的 `retranslate_ui()`，然后重建菜单栏。

### 7.3 翻译更新流程

1. `pylupdate6` 提取 `tr()` 字符串
2. 编辑 `resources/translations/zh_CN/app_zh_CN.ts`
3. `scripts/build_translations.py` 编译为 `.qm`

---

## 八、设计原则

1. **不引入新依赖** — 所有功能使用 PySide6 和 Python 标准库
2. **QSS 不硬编码** — 颜色通过 ThemeManager 和 theme JSON 控制
3. **所有文本走 i18n** — 使用 `self.tr()` 包裹
4. **保持向后兼容** — 新增表，不修改现有表结构
5. **信号驱动页面切换** — 页面通过 Signal/Slot 通信，不直接引用
