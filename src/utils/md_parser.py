import re


class MarkdownQuestionParser:
    """Parses Markdown-formatted exam questions into structured data.

    Expected format per question block (separated by '---'):
        ## Question N
        Question text...
        - A. Option text
        - B. Option text
        **Correct Answer: B**
        **Explanation:** ...
        **Related Content:**
        - 11.1.3 Topic Name
    """

    def __init__(self):
        self.questions = []

    def parse_file(self, md_content: str) -> list[dict]:
        """Parse Markdown content and return a list of question dicts."""
        self.questions = []

        for block in re.split(r'\n---\n', md_content):
            block = block.strip()
            if not block:
                continue
            question = self._parse_question_block(block)
            if question:
                self.questions.append(question)

        return self.questions

    def _parse_question_block(self, block: str) -> dict | None:
        """Parse a single question block into a structured dict."""

        # Question number
        num_match = re.search(r'^##\s+Question\s+(\d+)', block, re.MULTILINE)
        if not num_match:
            return None
        question_number = int(num_match.group(1))

        # Question text (between header and first option)
        text_match = re.search(
            r'##\s+Question\s+\d+\s*\n+(.*?)\n+- [A-Z]\.',
            block, re.DOTALL
        )
        if not text_match:
            return None
        question_text = text_match.group(1).strip()

        # Options
        options = []
        for match in re.finditer(r'^- ([A-Z])\.\s+(.+?)$', block, re.MULTILINE):
            options.append({
                'label': match.group(1),
                'text': match.group(2).strip(),
                'is_correct': False
            })

        # Correct answers
        answer_match = re.search(r'\*\*Correct Answer:\s*([A-Z](?:,\s*[A-Z])*)\*\*', block)
        if not answer_match:
            return None
        correct_answers = [a.strip() for a in answer_match.group(1).split(',')]

        is_multiple_choice = len(correct_answers) > 1

        for option in options:
            if option['label'] in correct_answers:
                option['is_correct'] = True

        # Explanation
        exp_match = re.search(
            r'\*\*Explanation:\*\*\s*\n+(.*?)\n+\*\*Related Content',
            block, re.DOTALL
        )
        explanation = exp_match.group(1).strip() if exp_match else ""

        # Related content
        related_content = []
        rel_match = re.search(r'\*\*Related Content:\*\*\s*\n+((?:- .+\n?)+)', block)
        if rel_match:
            related_content = [
                line.strip('- ').strip()
                for line in rel_match.group(1).strip().split('\n')
            ]

        return {
            'question_number': question_number,
            'question_text': question_text,
            'options': options,
            'correct_answers': correct_answers,
            'explanation': explanation,
            'related_content': related_content,
            'is_multiple_choice': is_multiple_choice
        }

    def get_chapter_from_content(self, related_content: list[str]) -> str | None:
        """Extract chapter number from related content (e.g. '11.1.3 Topic' -> '11.1')."""
        if not related_content:
            return None
        match = re.match(r'(\d+\.\d+)', related_content[0])
        return match.group(1) if match else None
