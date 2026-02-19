# ReCall - User Guide

## Quick Start

This section walks you through setting up the application from scratch.

### 1. First Launch

When you open the application for the first time, you will see an empty home page
with the message **"Set up your first exam to get started!"**. Click the
**Open Exam Manager** button to begin.

### 2. Create Your Exam Structure

In the Exam Manager window:

1. The app has created a default exam for you. Enter a name for it in the
   **Rename** field (e.g., "My Exam") and click **Save**.
2. Add modules by clicking **Add** under the Modules panel on the left
   (e.g., "Core 1", "Core 2"). Modules are top-level categories for organizing
   your questions.
3. Select a module, then add chapters on the right panel by clicking **Add**
   (e.g., Chapter 1.0 "Hardware", Chapter 1.1 "Cables and Connectors").

> **Tip:** If your exam does not need modules (only chapters), you can skip
> adding modules. The app will use a hidden default module automatically. In
> this case the Module filter on the home page is hidden.

### 3. Add Questions

There are two ways to add questions:

**Option A: Add Manually**

Go to **Admin > New Question Entry**. Fill in:
- Select the target module and chapter
- Enter the question text
- Choose question type: MC (Single Choice) or MR (Multiple Response)
- Add answer options and mark the correct one(s)
- Optionally add an explanation

Click **Save** to add the question.

**Option B: Batch Import from Markdown**

Go to **Admin > Batch Import from Markdown**. This lets you import many questions
at once from a `.md` file. See the [Markdown Import Format](#markdown-import-format)
section below for the required file format.

### 4. Start Practicing

Close the admin windows and return to the home page. You should now see the
**Practice Settings** area. Configure your session:

- **Learning Mode** - Check your answer after each question. See explanations
  immediately. No time pressure.
- **Exam Simulation** - Timed session. Answers are graded at the end, just like
  a real exam.

Select a module and chapter (or leave as "All"), set the number of questions,
and click **Start Practice**.

**Optional filters:**
- **Flagged Questions First** - Prioritizes questions you have flagged for review.
  If there are not enough flagged questions, the session is padded with random ones.
- **Wrong Questions First** - Prioritizes questions you have answered incorrectly
  before. If there are not enough wrong questions, the session is padded with
  random ones.

### 5. Review Results

After submitting your answers, the results page shows:
- Overall score and time spent
- Per-question review with your answer, the correct answer, and explanations
- Option to **Retry Wrong Questions** to focus on what you missed

---

## Detailed Usage

### Exam Management

Open via **Admin > Exam Manager**.

**Multiple Exams:**
The application supports multiple independent exam databases. Each exam has its
own questions, modules, chapters, and practice history.

- **New Exam** - Creates a new empty exam database. You will be switched to it
  automatically.
- **Switch Exams** - Use the dropdown at the top to switch between exams.
- **Rename** - Change the display name of the current exam.
- **Delete Exam** - Permanently removes an exam and all its data. You cannot
  delete the last remaining exam.

**Modules and Chapters:**

- Modules are the top-level grouping (e.g., "Core 1", "Core 2").
- Chapters belong to a module (e.g., "1.0 Hardware", "1.1 Cables").
- Main chapters (e.g., 1.0, 2.0) act as section headers. Sub-chapters
  (e.g., 1.1, 1.2) are the actual lesson units.
- You can add, rename, and delete modules and chapters at any time.

> **Note:** Deleting a module removes all its chapters and the links between
> chapters and questions. The questions themselves are not deleted.

### Question Management

**Adding Questions Manually:**
Open via **Admin > New Question Entry**. Each question requires:
- Question text
- At least 2 answer options
- At least 1 correct answer marked
- A target module and chapter

**Editing and Deleting Questions:**
Open via **Admin > Manage Questions (Edit/Delete)**. This window shows all
questions in a searchable table. You can:
- Filter by module and chapter
- Search by question text
- Edit any question's text, options, or correct answers
- Delete questions (with confirmation)
- Flag questions for review

**Batch Import:**
Open via **Admin > Batch Import from Markdown**.
1. Click **Browse** to select a `.md` file
2. Select the target module
3. Click **Parse File** to preview the questions
4. Click **Import Questions** to save them to the database

Duplicate questions (same text) are automatically skipped.

### Markdown Import Format

The batch import expects a specific Markdown format. Questions are separated
by `---` (horizontal rule). Each question block follows this structure:

```markdown
## Question 1
What is the primary function of a motherboard?

- A. Store data permanently
- B. Connect all computer components
- C. Generate electrical power
- D. Cool the processor

**Correct Answer: B**

**Explanation:**
The motherboard is the main circuit board that connects all components
of a computer, including the CPU, memory, and storage devices.

**Related Content:**
- 2.2 Motherboards

---

## Question 2
Which of the following are valid IP address classes? (Choose two)

- A. Class A
- B. Class E
- C. Class F
- D. Class G

**Correct Answer: A, B**

**Explanation:**
IP address classes include Class A through E. Classes F and G do not exist.

**Related Content:**
- 6.2 TCP/IP Concepts

---
```

**Format rules:**
- `## Question N` - Required header. Question type (MC/MR) is detected
  automatically: if there are multiple correct answers, it is treated as MR.
- `- A. Option text` - Options must start with `- ` followed by a capital
  letter and period.
- `**Correct Answer: B**` - Single letter for MC, comma-separated for MR
  (e.g., `A, C`).
- `**Explanation:**` - Optional but recommended.
- `**Related Content:**` - Optional. The chapter number (e.g., `2.2`) is used
  to link the question to the correct chapter.
- `---` - Separates question blocks.

### Practice Modes

**Learning Mode:**
- Answer at your own pace
- Click **Check** to verify your answer immediately
- Correct options are highlighted in green, incorrect selections in red
- Explanation is shown after checking
- Navigate freely between questions with Previous/Next

**Exam Simulation:**
- Time limit is automatically set to **1 minute per question** (e.g., 20
  questions → 20-minute session). The calculated limit is shown on the home page
  before you start.
- Timer counts down in the top-right corner
- Mark questions for review with the **Mark** button (session-only; marks are
  not saved after the session ends)
- Submit when ready, or answers are auto-submitted when time expires
- Unanswered and marked questions are summarized before submission
- Results are shown after submission (no mid-exam feedback)

**After Practice:**
- View your score and time breakdown
- Expand each question to see your answer vs. the correct answer
- Click **Retry Wrong Questions** to practice only the ones you missed
- Click **New Practice** to return to the home page

### Statistics

The home page displays your learning progress:
- Total questions practiced and overall accuracy
- Last session score
- Per-module accuracy bars (click **Show Details** to expand)
- Weak areas are highlighted automatically (modules below 60% accuracy)

To reset all statistics: **Admin > Reset Statistics**.

### Themes

Go to **View > Theme** to switch between:
- **Default** - Light theme
- **Dark** - Dark theme for low-light environments

### Font Size

Go to **View > Font Size** to choose from:
- Small (8pt), Normal (10pt), Large (12pt), Extra Large (14pt), Huge (16pt)

### Language

Go to **Language** menu to switch between:
- **English** (en_US)
- **Chinese** (zh_CN)

The interface updates immediately without restarting the application.

---

## FAQ

**Q: I started the app but there are no questions. What do I do?**
A: Click "Open Exam Manager" on the home page. Create your exam structure
(modules and chapters), then add questions via Admin > New Question Entry
or Admin > Batch Import from Markdown.

**Q: Can I have multiple exams at the same time?**
A: Yes. Open Admin > Exam Manager and click "New Exam" to create additional
exam databases. Switch between them using the dropdown.

**Q: How do I import questions from another source?**
A: Format your questions as a Markdown file following the
[Markdown Import Format](#markdown-import-format) described above, then use
Admin > Batch Import from Markdown.

**Q: What happens if I import duplicate questions?**
A: The importer automatically detects and skips questions with identical text.
A summary is shown after import.

**Q: "No matching questions found" when I start practice. Why?**
A: There are no questions in the selected module or chapter. Check that you
have added questions to the database, and that your module/chapter filters
match where those questions are stored.

**Q: What do "Flagged Questions First" and "Wrong Questions First" do?**
A: These are priority filters, not exclusive filters. When either is checked,
the session loads those questions first. If there are not enough to fill your
requested count, the remaining slots are filled with random questions from the
same module/chapter scope.

**Q: Where is my data stored?**
A: Exam databases (`.db` files) are stored in the `data/` folder next to the
application. Each exam is a separate SQLite file. You can back up your data
by copying these files.

**Q: Can I move my data to another computer?**
A: Yes. Copy the `.db` files from the `data/` folder to the same location on
the other computer. The app will detect them automatically on startup.

**Q: How do I open this guide again later?**
A: Go to **Help > User Guide** from the menu bar at any time.
