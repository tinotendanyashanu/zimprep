import { ExamPaper } from "./types";

export const MOCK_PAPER: ExamPaper = {
    id: "mock-paper-1",
    title: "English Language - Paper 1 (Narrative)",
    subject: "English Language",
    durationMinutes: 90,
    totalMarks: 50,
    instructions: [
        "Answer all questions.",
        "Your composition should be between 350 and 450 words.",
        "Pay attention to punctuation, spelling, and grammar.",
        "Write clearly and legibly."
    ],
    questions: [
        {
            id: "q1",
            text: `
                <h3>Section A: Free Composition (50 Marks)</h3>
                <p>Write a composition on <strong>one</strong> of the following topics:</p>
                <ol>
                    <li>Write a story ending with the words: "...and that was the last time I saw him."</li>
                    <li>Describe an occasion when you were very frightened.</li>
                    <li>"Technology has done more harm than good." Discuss.</li>
                    <li>Write a letter to the editor of a local newspaper complaining about the poor state of roads in your area.</li>
                </ol>
            `,
            marks: 50,
            type: "essay"
        }
        // In a real scenario we'd have more, but for Phase 3 focus, one rich question is good for essay/writing testing.
    ]
};

// Helper for generating more questions if needed
export const getMockPaper = (id: string): ExamPaper => {
    return MOCK_PAPER;
};
