import glob
import os
import sqlite3
import sys
from datetime import datetime, date


class DBManager:
    """Manages all SQLite database connections, initialization, and CRUD operations."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = self._resolve_default_db_path()

            # If configured db doesn't exist, try to find any existing .db file
            if not os.path.exists(db_path):
                data_dir = os.path.dirname(db_path)
                existing = sorted(glob.glob(os.path.join(data_dir, '*.db')))
                if existing:
                    db_path = existing[0]

        self._connect(db_path)

    def _connect(self, db_path: str):
        """Open a connection to the given database file and initialize tables."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    @staticmethod
    def _resolve_default_db_path() -> str:
        """Resolve the default database path.

        When frozen (PyInstaller), the data/ folder lives next to the .exe.
        When running from source, it lives in the project root.
        """
        if getattr(sys, 'frozen', False):
            # Frozen: put data/ next to the .exe, not inside _MEIPASS
            base_dir = os.path.dirname(sys.executable)
        else:
            try:
                from src.core.config import Config
                config = Config()
                return config.get_absolute_path(
                    config.get('database.path', 'data/default.db')
                )
            except Exception as e:
                print(f"Warning: Could not load database path from config: {e}")
                from src.core.config import get_project_root
                base_dir = get_project_root()
        return os.path.join(base_dir, 'data', 'default.db')

    def create_tables(self):
        """Create all database tables if they don't exist."""

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Knowledge_Modules (
                module_id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT NOT NULL UNIQUE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Lessons (
                lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                chapter_num TEXT NOT NULL,
                chapter_title TEXT NOT NULL,
                is_chapter_level BOOLEAN NOT NULL,
                FOREIGN KEY (module_id) REFERENCES Knowledge_Modules(module_id) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                explanation TEXT,
                question_type TEXT DEFAULT 'MC' NOT NULL,
                is_flagged BOOLEAN DEFAULT 0
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Answers (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Question_Usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE,
                FOREIGN KEY (lesson_id) REFERENCES Lessons(lesson_id) ON DELETE CASCADE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS UserSettings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Practice_Sessions (
                session_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id     INTEGER,
                mode          TEXT NOT NULL DEFAULT 'learn',
                total_count   INTEGER NOT NULL DEFAULT 0,
                correct_count INTEGER NOT NULL DEFAULT 0,
                duration_sec  INTEGER DEFAULT 0,
                started_at    TEXT NOT NULL,
                finished_at   TEXT,
                FOREIGN KEY (module_id) REFERENCES Knowledge_Modules(module_id)
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Answer_Records (
                record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id    INTEGER NOT NULL,
                question_id   INTEGER NOT NULL,
                user_answer   TEXT,
                is_correct    INTEGER NOT NULL DEFAULT 0,
                time_spent    INTEGER DEFAULT 0,
                answered_at   TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES Practice_Sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE
            );
        """)

        self.conn.commit()

    # --- Module & Lesson helpers ---

    def insert_knowledge_module(self, module_name: str) -> int | None:
        """Insert or retrieve a knowledge module ID."""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO Knowledge_Modules (module_name) VALUES (?)",
                (module_name,)
            )
            self.conn.commit()
            self.cursor.execute(
                "SELECT module_id FROM Knowledge_Modules WHERE module_name = ?",
                (module_name,)
            )
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Failed to insert knowledge module: {e}")
            return None

    def insert_lesson(self, module_id: int, chapter_num: str, chapter_title: str,
                      is_chapter_level: bool) -> int | None:
        """Insert a lesson/chapter entry."""
        try:
            sql = """
                INSERT INTO Lessons (module_id, chapter_num, chapter_title, is_chapter_level)
                VALUES (?, ?, ?, ?)
            """
            self.cursor.execute(sql, (module_id, chapter_num, chapter_title, is_chapter_level))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Failed to insert lesson: {e}")
            return None

    def get_all_modules(self):
        """Get all knowledge modules as [(module_id, module_name), ...]."""
        self.cursor.execute(
            "SELECT module_id, module_name FROM Knowledge_Modules ORDER BY module_id"
        )
        return self.cursor.fetchall()

    def get_lessons_by_module(self, module_id: int):
        """Get all lessons for a module as [(lesson_id, chapter_num, chapter_title), ...]."""
        sql = """
            SELECT lesson_id, chapter_num, chapter_title
            FROM Lessons
            WHERE module_id = ?
            ORDER BY CAST(chapter_num AS REAL)
        """
        self.cursor.execute(sql, (module_id,))
        return self.cursor.fetchall()

    def get_lesson_id_by_chapter(self, module_id: int, chapter_num: str) -> int | None:
        """Get lesson_id by module ID and chapter number."""
        sql = """
            SELECT lesson_id FROM Lessons
            WHERE module_id = ? AND chapter_num = ?
            LIMIT 1
        """
        self.cursor.execute(sql, (module_id, chapter_num))
        result = self.cursor.fetchone()
        return result[0] if result else None

    # --- Question CRUD ---

    def get_question_with_answers(self, question_id: int) -> dict | None:
        """Get a question with all its answer options."""
        self.cursor.execute("""
            SELECT question_id, question_text, explanation, question_type, is_flagged
            FROM Questions WHERE question_id = ?
        """, (question_id,))
        q_row = self.cursor.fetchone()

        if not q_row:
            return None

        question = {
            'question_id': q_row[0],
            'question_text': q_row[1],
            'explanation': q_row[2],
            'question_type': q_row[3],
            'is_flagged': bool(q_row[4]),
            'answers': []
        }

        self.cursor.execute("""
            SELECT answer_id, option_text, is_correct
            FROM Answers WHERE question_id = ?
        """, (question_id,))

        for a_row in self.cursor.fetchall():
            question['answers'].append({
                'answer_id': a_row[0],
                'option_text': a_row[1],
                'is_correct': bool(a_row[2])
            })

        return question

    def insert_full_question(self, question_data: dict, answers_data: list,
                             lesson_id: int) -> int | None:
        """Insert a complete question (text, options, usage) in a single transaction."""
        try:
            with self.conn:
                self.cursor.execute("""
                    INSERT INTO Questions (question_text, explanation, question_type, is_flagged)
                    VALUES (?, ?, ?, ?)
                """, (
                    question_data.get('question_text', ''),
                    question_data.get('explanation'),
                    question_data.get('question_type', 'MC'),
                    question_data.get('is_flagged', 0)
                ))
                new_question_id = self.cursor.lastrowid

                answers_to_insert = [
                    (new_question_id, a['option_text'], a.get('is_correct', 0))
                    for a in answers_data
                ]
                self.cursor.executemany("""
                    INSERT INTO Answers (question_id, option_text, is_correct)
                    VALUES (?, ?, ?)
                """, answers_to_insert)

                self.cursor.execute("""
                    INSERT INTO Question_Usage (question_id, lesson_id)
                    VALUES (?, ?)
                """, (new_question_id, lesson_id))

            return new_question_id

        except sqlite3.Error as e:
            print(f"Failed to insert question, transaction rolled back: {e}")
            return None

    def check_duplicate_question(self, question_text: str) -> bool:
        """Check if a question with the same text already exists."""
        normalized_text = question_text.strip()
        sql = "SELECT EXISTS(SELECT 1 FROM Questions WHERE question_text = ? LIMIT 1)"
        self.cursor.execute(sql, (normalized_text,))
        return self.cursor.fetchone()[0] == 1

    def update_question(self, question_id: int, question_data: dict,
                        answers_data: list) -> bool:
        """Update a question's text, options, and metadata in a single transaction."""
        try:
            with self.conn:
                self.cursor.execute("""
                    UPDATE Questions
                    SET question_text = ?, explanation = ?, question_type = ?, is_flagged = ?
                    WHERE question_id = ?
                """, (
                    question_data.get('question_text', ''),
                    question_data.get('explanation'),
                    question_data.get('question_type', 'MC'),
                    question_data.get('is_flagged', 0),
                    question_id
                ))

                self.cursor.execute("DELETE FROM Answers WHERE question_id = ?", (question_id,))

                answers_to_insert = [
                    (question_id, a['option_text'], a.get('is_correct', 0))
                    for a in answers_data
                ]
                self.cursor.executemany("""
                    INSERT INTO Answers (question_id, option_text, is_correct)
                    VALUES (?, ?, ?)
                """, answers_to_insert)

            return True

        except sqlite3.Error as e:
            print(f"Failed to update question, transaction rolled back: {e}")
            return False

    def delete_question(self, question_id: int) -> bool:
        """Delete a question (cascades to answers and usage records)."""
        try:
            self.cursor.execute("DELETE FROM Questions WHERE question_id = ?", (question_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Failed to delete question: {e}")
            self.conn.rollback()
            return False

    # --- Question listing & search ---

    def get_questions_list(self, module_id: int | None = None, chapter_num: str | None = None,
                          search_text: str | None = None, offset: int = 0,
                          limit: int = 50) -> list[dict]:
        """Get a paginated list of questions with optional filters."""
        sql_parts = ["""
            SELECT DISTINCT
                Q.question_id, Q.question_text, Q.question_type, Q.is_flagged,
                KM.module_name, L.chapter_num, L.chapter_title
            FROM Questions Q
            LEFT JOIN Question_Usage QU ON Q.question_id = QU.question_id
            LEFT JOIN Lessons L ON QU.lesson_id = L.lesson_id
            LEFT JOIN Knowledge_Modules KM ON L.module_id = KM.module_id
        """]

        where_clauses = []
        params = []

        if module_id is not None:
            where_clauses.append("L.module_id = ?")
            params.append(module_id)
        if chapter_num:
            where_clauses.append("L.chapter_num = ?")
            params.append(chapter_num)
        if search_text:
            where_clauses.append("Q.question_text LIKE ?")
            params.append(f"%{search_text}%")

        if where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))

        sql_parts.append("ORDER BY Q.question_id DESC")
        sql_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])

        try:
            self.cursor.execute(" ".join(sql_parts), tuple(params))
            rows = self.cursor.fetchall()
            return [{
                'question_id': r[0],
                'question_text': r[1][:100] + '...' if len(r[1]) > 100 else r[1],
                'full_text': r[1],
                'question_type': r[2],
                'is_flagged': bool(r[3]),
                'module_name': r[4] or 'Unknown',
                'chapter_num': r[5] or 'N/A',
                'chapter_title': r[6] or 'N/A'
            } for r in rows]
        except Exception as e:
            print(f"Failed to get questions list: {e}")
            return []

    def get_total_questions_count(self, module_id: int | None = None,
                                  chapter_num: str | None = None,
                                  search_text: str | None = None) -> int:
        """Get total question count matching filters (for pagination)."""
        sql_parts = ["""
            SELECT COUNT(DISTINCT Q.question_id)
            FROM Questions Q
            LEFT JOIN Question_Usage QU ON Q.question_id = QU.question_id
            LEFT JOIN Lessons L ON QU.lesson_id = L.lesson_id
        """]

        where_clauses = []
        params = []

        if module_id is not None:
            where_clauses.append("L.module_id = ?")
            params.append(module_id)
        if chapter_num:
            where_clauses.append("L.chapter_num = ?")
            params.append(chapter_num)
        if search_text:
            where_clauses.append("Q.question_text LIKE ?")
            params.append(f"%{search_text}%")

        if where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))

        try:
            self.cursor.execute(" ".join(sql_parts), tuple(params))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"Failed to get question count: {e}")
            return 0

    # --- Batch import ---

    def batch_insert_questions(self, questions_data: list, module_id: int) -> dict:
        """Batch import questions with automatic deduplication.

        Args:
            questions_data: Parsed question list from MarkdownQuestionParser.
            module_id: Target knowledge module ID.

        Returns:
            Dict with 'success', 'skipped', 'failed' counts and 'details' list.
        """
        from src.utils.md_parser import MarkdownQuestionParser

        parser = MarkdownQuestionParser()
        result = {'success': 0, 'skipped': 0, 'failed': 0, 'details': []}

        for idx, q_data in enumerate(questions_data, 1):
            question_text = q_data['question_text']

            if self.check_duplicate_question(question_text):
                result['skipped'] += 1
                result['details'].append({
                    'index': idx, 'status': 'skipped',
                    'reason': 'Duplicate question text'
                })
                continue

            chapter_num = parser.get_chapter_from_content(q_data.get('related_content', []))
            if not chapter_num:
                result['failed'] += 1
                result['details'].append({
                    'index': idx, 'status': 'failed',
                    'reason': 'Cannot extract chapter number'
                })
                continue

            lesson_id = self.get_lesson_id_by_chapter(module_id, chapter_num)
            if not lesson_id:
                result['failed'] += 1
                result['details'].append({
                    'index': idx, 'status': 'failed',
                    'reason': f'Chapter {chapter_num} not found in database'
                })
                continue

            question_dict = {
                'question_text': question_text,
                'explanation': q_data.get('explanation', ''),
                'question_type': 'MR' if q_data.get('is_multiple_choice') else 'MC',
                'is_flagged': 0
            }
            answers_list = [{
                'option_text': opt['text'],
                'is_correct': 1 if opt['is_correct'] else 0
            } for opt in q_data.get('options', [])]

            new_id = self.insert_full_question(question_dict, answers_list, lesson_id)

            if new_id:
                result['success'] += 1
                result['details'].append({
                    'index': idx, 'status': 'success',
                    'question_id': new_id, 'chapter': chapter_num
                })
            else:
                result['failed'] += 1
                result['details'].append({
                    'index': idx, 'status': 'failed',
                    'reason': 'Database insert error'
                })

        return result

    # --- Random question selection ---

    def get_random_question_ids(self, module_id: int | None, chapter_numbers: list[str] | None,
                                count: int, is_flagged: bool,
                                exclude_ids: list[int] | None = None) -> list[int]:
        """Randomly select question IDs based on filters.

        chapter_numbers: e.g. ['1.1', '1.2', '2.1']. A main chapter like '1.0'
        automatically expands to include all sub-chapters (1.1, 1.2, etc.).
        exclude_ids: question IDs to exclude (used when filling up after a filtered query).
        """
        sql_parts = [
            "SELECT DISTINCT Q.question_id FROM Questions Q",
            "JOIN Question_Usage QU ON Q.question_id = QU.question_id",
            "JOIN Lessons L ON QU.lesson_id = L.lesson_id"
        ]

        where_clauses = []
        params = []

        if is_flagged:
            where_clauses.append("Q.is_flagged = 1")

        if chapter_numbers:
            chapter_conditions = []
            for chapter_num in chapter_numbers:
                if chapter_num.endswith('.0'):
                    major_num = chapter_num.split('.')[0]
                    chapter_conditions.append("L.chapter_num LIKE ?")
                    params.append(f"{major_num}.%")
                else:
                    chapter_conditions.append("L.chapter_num = ?")
                    params.append(chapter_num)
            if chapter_conditions:
                where_clauses.append(f"({' OR '.join(chapter_conditions)})")

        if module_id is not None:
            where_clauses.append("L.module_id = ?")
            params.append(module_id)

        if exclude_ids:
            placeholders = ",".join("?" for _ in exclude_ids)
            where_clauses.append(f"Q.question_id NOT IN ({placeholders})")
            params.extend(exclude_ids)

        if where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))

        sql_parts.append("ORDER BY RANDOM() LIMIT ?")
        params.append(count)

        try:
            self.cursor.execute(" ".join(sql_parts), tuple(params))
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Failed to get random question IDs: {e}")
            return []

    # --- Practice session tracking ---

    def create_practice_session(self, module_id: int | None, mode: str,
                                total_count: int) -> int | None:
        """Create a new practice session and return session_id."""
        try:
            sql = """
                INSERT INTO Practice_Sessions (module_id, mode, total_count, started_at)
                VALUES (?, ?, ?, ?)
            """
            self.cursor.execute(sql, (module_id, mode, total_count, datetime.now().isoformat()))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Failed to create practice session: {e}")
            return None

    def finish_practice_session(self, session_id: int, correct_count: int,
                                duration_sec: int) -> bool:
        """Finish a practice session by updating score and duration."""
        try:
            sql = """
                UPDATE Practice_Sessions
                SET correct_count = ?, duration_sec = ?, finished_at = ?
                WHERE session_id = ?
            """
            self.cursor.execute(sql, (
                correct_count, duration_sec, datetime.now().isoformat(), session_id
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Failed to finish practice session: {e}")
            return False

    def save_answer_record(self, session_id: int, question_id: int, user_answer: str,
                           is_correct: bool, time_spent: int) -> bool:
        """Save an individual answer record."""
        try:
            sql = """
                INSERT INTO Answer_Records
                    (session_id, question_id, user_answer, is_correct, time_spent, answered_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql, (
                session_id, question_id, user_answer,
                1 if is_correct else 0, time_spent, datetime.now().isoformat()
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Failed to save answer record: {e}")
            return False

    # --- Statistics ---

    def get_question_count(self) -> int:
        """Get total number of questions in the database."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM Questions")
            return self.cursor.fetchone()[0]
        except sqlite3.Error:
            return 0

    def get_total_practiced_count(self) -> int:
        """Get total number of questions practiced across all sessions."""
        try:
            self.cursor.execute(
                "SELECT COALESCE(SUM(total_count), 0) FROM Practice_Sessions "
                "WHERE finished_at IS NOT NULL"
            )
            return self.cursor.fetchone()[0]
        except sqlite3.Error:
            return 0

    def get_overall_accuracy(self) -> float:
        """Get overall accuracy percentage (0.0 - 100.0)."""
        try:
            self.cursor.execute("""
                SELECT COALESCE(SUM(correct_count), 0), COALESCE(SUM(total_count), 0)
                FROM Practice_Sessions WHERE finished_at IS NOT NULL
            """)
            correct, total = self.cursor.fetchone()
            return (correct / total * 100) if total > 0 else 0.0
        except sqlite3.Error:
            return 0.0

    def get_recent_sessions(self, limit: int = 5) -> list[dict]:
        """Get the most recent N completed practice sessions."""
        try:
            sql = """
                SELECT ps.session_id, ps.mode, ps.total_count, ps.correct_count,
                       ps.duration_sec, ps.started_at, ps.finished_at, km.module_name
                FROM Practice_Sessions ps
                LEFT JOIN Knowledge_Modules km ON ps.module_id = km.module_id
                WHERE ps.finished_at IS NOT NULL
                ORDER BY ps.started_at DESC
                LIMIT ?
            """
            self.cursor.execute(sql, (limit,))
            return [{
                'session_id': r[0], 'mode': r[1], 'total_count': r[2],
                'correct_count': r[3], 'duration_sec': r[4],
                'started_at': r[5], 'finished_at': r[6],
                'module_name': r[7] or 'All Modules'
            } for r in self.cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_module_accuracy(self) -> list[dict]:
        """Get accuracy and session count per module."""
        try:
            sql = """
                SELECT km.module_id, km.module_name,
                       COUNT(ps.session_id) as session_count,
                       COALESCE(SUM(ps.correct_count), 0) as total_correct,
                       COALESCE(SUM(ps.total_count), 0) as total_questions
                FROM Knowledge_Modules km
                LEFT JOIN Practice_Sessions ps
                    ON km.module_id = ps.module_id AND ps.finished_at IS NOT NULL
                GROUP BY km.module_id, km.module_name
                ORDER BY km.module_id
            """
            self.cursor.execute(sql)
            return [{
                'module_id': r[0], 'module_name': r[1],
                'session_count': r[2], 'total_correct': r[3],
                'total_questions': r[4],
                'accuracy': (r[3] / r[4] * 100) if r[4] > 0 else 0.0
            } for r in self.cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_wrong_question_ids(self, module_id: int | None = None,
                                chapter_numbers: list[str] | None = None,
                                limit: int = 50) -> list[int]:
        """Get IDs of incorrectly answered questions (based on most recent attempt)."""
        try:
            sql_parts = ["""
                SELECT ar.question_id
                FROM Answer_Records ar
                INNER JOIN (
                    SELECT question_id, MAX(record_id) as latest_record
                    FROM Answer_Records GROUP BY question_id
                ) latest ON ar.record_id = latest.latest_record
                WHERE ar.is_correct = 0
            """]
            params = []

            if module_id is not None or chapter_numbers:
                sql_parts.append("""
                    AND ar.question_id IN (
                        SELECT DISTINCT qu.question_id FROM Question_Usage qu
                        JOIN Lessons l ON qu.lesson_id = l.lesson_id
                        WHERE 1=1
                """)
                if module_id is not None:
                    sql_parts.append("AND l.module_id = ?")
                    params.append(module_id)
                if chapter_numbers:
                    placeholders = ",".join(["?" for _ in chapter_numbers])
                    sql_parts.append(f"AND l.chapter_num IN ({placeholders})")
                    params.extend(chapter_numbers)
                sql_parts.append(")")

            sql_parts.append("ORDER BY ar.record_id DESC LIMIT ?")
            params.append(limit)

            self.cursor.execute(" ".join(sql_parts), tuple(params))
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Failed to get wrong question IDs: {e}")
            return []

    def get_today_stats(self) -> dict:
        """Get today's practice count and accuracy."""
        try:
            today = date.today().isoformat()
            sql = """
                SELECT COALESCE(SUM(total_count), 0), COALESCE(SUM(correct_count), 0)
                FROM Practice_Sessions
                WHERE finished_at IS NOT NULL AND DATE(started_at) = ?
            """
            self.cursor.execute(sql, (today,))
            total, correct = self.cursor.fetchone()
            return {
                'total': total, 'correct': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0.0
            }
        except sqlite3.Error:
            return {'total': 0, 'correct': 0, 'accuracy': 0.0}

    def reset_practice_stats(self) -> bool:
        """Delete all practice sessions and answer records."""
        try:
            self.cursor.execute("DELETE FROM Answer_Records")
            self.cursor.execute("DELETE FROM Practice_Sessions")
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Failed to reset practice stats: {e}")
            return False

    # --- Exam name ---

    def get_exam_name(self) -> str:
        """Get the exam display name from UserSettings, fallback to DB filename."""
        try:
            self.cursor.execute("SELECT value FROM UserSettings WHERE key = 'exam_name'")
            row = self.cursor.fetchone()
            if row and row[0]:
                return row[0]
        except sqlite3.Error:
            pass
        return os.path.splitext(os.path.basename(self.db_path))[0]

    def set_exam_name(self, name: str) -> bool:
        """Store the exam display name in UserSettings."""
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO UserSettings (key, value) VALUES ('exam_name', ?)",
                (name,)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Failed to set exam name: {e}")
            return False

    # --- Module & Lesson CRUD (admin) ---

    def add_module(self, name: str) -> int | None:
        """Add a new knowledge module. Returns module_id or None if duplicate."""
        try:
            self.cursor.execute(
                "INSERT INTO Knowledge_Modules (module_name) VALUES (?)", (name,)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        except sqlite3.Error as e:
            print(f"Failed to add module: {e}")
            return None

    def rename_module(self, module_id: int, new_name: str) -> bool:
        """Rename a knowledge module."""
        try:
            self.cursor.execute(
                "UPDATE Knowledge_Modules SET module_name = ? WHERE module_id = ?",
                (new_name, module_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Failed to rename module: {e}")
            return False

    def delete_module(self, module_id: int) -> bool:
        """Delete a module and cascade to its lessons and question associations."""
        try:
            self.cursor.execute(
                "DELETE FROM Knowledge_Modules WHERE module_id = ?", (module_id,)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Failed to delete module: {e}")
            return False

    def add_lesson(self, module_id: int, chapter_num: str, chapter_title: str,
                   is_chapter_level: bool) -> int | None:
        """Add a new lesson/chapter to a module."""
        try:
            self.cursor.execute(
                "INSERT INTO Lessons (module_id, chapter_num, chapter_title, is_chapter_level) "
                "VALUES (?, ?, ?, ?)",
                (module_id, chapter_num, chapter_title, is_chapter_level)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Failed to add lesson: {e}")
            return None

    def update_lesson(self, lesson_id: int, chapter_num: str, chapter_title: str) -> bool:
        """Update a lesson's chapter number and title."""
        try:
            self.cursor.execute(
                "UPDATE Lessons SET chapter_num = ?, chapter_title = ? WHERE lesson_id = ?",
                (chapter_num, chapter_title, lesson_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Failed to update lesson: {e}")
            return False

    def delete_lesson(self, lesson_id: int) -> bool:
        """Delete a lesson (cascades to question_usage)."""
        try:
            self.cursor.execute("DELETE FROM Lessons WHERE lesson_id = ?", (lesson_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Failed to delete lesson: {e}")
            return False

    def get_or_create_default_module(self) -> int:
        """Get or create the hidden default module for module-less exams."""
        try:
            self.cursor.execute(
                "SELECT module_id FROM Knowledge_Modules WHERE module_name = '_default'"
            )
            row = self.cursor.fetchone()
            if row:
                return row[0]
            self.cursor.execute(
                "INSERT INTO Knowledge_Modules (module_name) VALUES ('_default')"
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Failed to get/create default module: {e}")
            return None

    def get_visible_modules(self):
        """Get all modules except the hidden default, as [(module_id, module_name), ...]."""
        self.cursor.execute(
            "SELECT module_id, module_name FROM Knowledge_Modules "
            "WHERE module_name != '_default' ORDER BY module_id"
        )
        return self.cursor.fetchall()

    def get_all_lessons(self):
        """Get all lessons across all modules as [(lesson_id, chapter_num, chapter_title), ...]."""
        sql = """
            SELECT lesson_id, chapter_num, chapter_title
            FROM Lessons
            ORDER BY CAST(chapter_num AS REAL)
        """
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    # --- Connection management ---

    def reopen(self, db_path: str):
        """Close current connection and open a new database."""
        self.close()
        self._connect(db_path)

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
