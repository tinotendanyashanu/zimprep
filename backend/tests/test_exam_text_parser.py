from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.exam_text_parser import parse_exam_text


class ExamTextParserTests(unittest.TestCase):
    def test_parses_mcq_and_ignores_headers_and_footers(self) -> None:
        raw_text = """
        INSTRUCTIONS
        Answer all questions.
        Page 2 of 12
        1 What is the capital of Zimbabwe? [1]
        A Harare
        B Bulawayo
        C Mutare
        D Gweru
        Turn over
        """

        parsed = parse_exam_text(raw_text)

        self.assertEqual(parsed["paper_type"], "mcq")
        self.assertEqual(len(parsed["questions"]), 1)
        question = parsed["questions"][0]
        self.assertEqual(question["question_number"], 1)
        self.assertEqual(question["text"], "What is the capital of Zimbabwe?")
        self.assertEqual(question["marks"], 1)
        self.assertEqual(
            question["options"],
            {"A": "Harare", "B": "Bulawayo", "C": "Mutare", "D": "Gweru"},
        )

    def test_parses_theory_hierarchy_and_total_marks(self) -> None:
        raw_text = """
        2 Answer the questions that follow. [Total: 7]
        (a) State the function of the xylem. [2]
        (b) Explain why transpiration is important.
        (i) Name one factor that increases transpiration. [1]
        (ii) State one precaution in the experiment. [1]
        """

        parsed = parse_exam_text(raw_text)

        self.assertEqual(parsed["paper_type"], "theory")
        question = parsed["questions"][0]
        self.assertEqual(question["marks"], 7)
        self.assertEqual(len(question["sub_questions"]), 2)
        self.assertEqual(question["sub_questions"][0]["id"], "a")
        self.assertEqual(question["sub_questions"][0]["marks"], 2)
        self.assertEqual(question["sub_questions"][1]["id"], "b")
        self.assertEqual(len(question["sub_questions"][1]["sub_questions"]), 2)
        self.assertEqual(question["sub_questions"][1]["sub_questions"][0]["id"], "i")
        self.assertEqual(question["sub_questions"][1]["sub_questions"][0]["marks"], 1)

    def test_parses_practical_question_with_multi_page_continuation(self) -> None:
        raw_text = """
        3 Fig. 1.1 shows the apparatus used in an experiment.
        Describe how the apparatus is set up.
        3
        Table 2.1 gives the results.
        State two conclusions. [4]
        Qualitative analysis
        carbonate gives carbon dioxide
        """

        parsed = parse_exam_text(raw_text)

        self.assertEqual(parsed["paper_type"], "practical")
        self.assertEqual(len(parsed["questions"]), 1)
        question = parsed["questions"][0]
        self.assertTrue(question["has_diagram"])
        self.assertTrue(question["has_table"])
        self.assertEqual(question["figure_refs"], ["Fig. 1.1"])
        self.assertEqual(question["table_refs"], ["Table 2.1"])
        self.assertEqual(question["marks"], 4)
        self.assertNotIn("Qualitative analysis", question["text"])


    def test_parses_question_with_q_prefix(self) -> None:
        raw_text = """
        Q1 What is photosynthesis? [3]
        A The process by which plants make food
        B The process by which plants breathe
        C The process by which plants grow
        D The process by which plants reproduce
        """
        parsed = parse_exam_text(raw_text)
        self.assertEqual(parsed["paper_type"], "mcq")
        self.assertEqual(len(parsed["questions"]), 1)
        self.assertEqual(parsed["questions"][0]["question_number"], 1)
        self.assertEqual(parsed["questions"][0]["marks"], 3)

    def test_handles_parenthesised_marks(self) -> None:
        raw_text = """
        1 Describe the structure of the cell membrane. (4 marks)
        """
        parsed = parse_exam_text(raw_text)
        self.assertEqual(parsed["questions"][0]["marks"], 4)

    def test_filters_dashed_page_numbers(self) -> None:
        raw_text = """
        — 3 —
        1 State two functions of the liver. [2]
        """
        parsed = parse_exam_text(raw_text)
        self.assertEqual(len(parsed["questions"]), 1)
        self.assertEqual(parsed["questions"][0]["question_number"], 1)

    def test_filters_ucles_and_zimsec_footers(self) -> None:
        raw_text = """
        1 Calculate the speed of sound. [3]
        UCLES 2024
        ZIMSEC 2023
        """
        parsed = parse_exam_text(raw_text)
        self.assertEqual(len(parsed["questions"]), 1)
        self.assertNotIn("UCLES", parsed["questions"][0]["text"])

    def test_multiple_questions_theory(self) -> None:
        raw_text = """
        1 State the law of conservation of energy. [2]
        2 Explain why metals are good conductors of electricity. [3]
        3 Describe the process of distillation. [4]
        """
        parsed = parse_exam_text(raw_text)
        self.assertEqual(parsed["paper_type"], "theory")
        self.assertEqual(len(parsed["questions"]), 3)
        self.assertEqual(parsed["questions"][0]["marks"], 2)
        self.assertEqual(parsed["questions"][1]["marks"], 3)
        self.assertEqual(parsed["questions"][2]["marks"], 4)

    def test_multi_page_continuation_with_page_number_in_middle(self) -> None:
        """Page numbers between question lines should not split a question."""
        raw_text = """
        1 Explain the following terms:
        (a) Osmosis [2]
        4
        (b) Diffusion [2]
        """
        parsed = parse_exam_text(raw_text)
        self.assertEqual(len(parsed["questions"]), 1)
        self.assertEqual(len(parsed["questions"][0]["sub_questions"]), 2)
        self.assertEqual(parsed["questions"][0]["sub_questions"][1]["id"], "b")


if __name__ == "__main__":
    unittest.main()
