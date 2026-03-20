import { ExamPaper } from "./types";

export const MOCK_PAPER: ExamPaper = {
    id: "mock-paper-1",
    title: "History - Paper 1 (2023)",
    subject: "History",
    level: "O",
    year: 2023,
    paperNumber: 1,
    durationMinutes: 90,
    totalMarks: 40,
    instructions: [
        "Answer ALL questions.",
        "Write your answers in the spaces provided.",
        "All working must be clearly shown.",
        "Start each question on a new page.",
    ],
    questions: [
        {
            id: "q1",
            questionNumber: "1",
            text: `<p>Explain the main causes of the First World War. In your answer, refer to the assassination of Archduke Franz Ferdinand and the alliance system in Europe.</p>`,
            marks: 10,
            type: "essay",
            topic: "World War I",
        },
        {
            id: "q2",
            questionNumber: "2",
            text: `<p>Study the source below and answer the question that follows.</p>
                   <blockquote class="border-l-4 border-zinc-300 pl-4 italic text-zinc-600 my-3">
                   "The League of Nations was doomed to fail because the United States refused to join, leaving it without the support of the world's most powerful nation." — Historian A, 1945
                   </blockquote>
                   <p>How far do you agree with this view about why the League of Nations failed? Use the source and your own knowledge.</p>`,
            marks: 12,
            type: "structured",
            topic: "League of Nations",
            has_image: true,
            imageUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/League_of_Nations_Anachronous_Map.png/640px-League_of_Nations_Anachronous_Map.png",
        },
        {
            id: "q3",
            questionNumber: "3",
            text: `<p>Which of the following was the MAIN cause of the Great Depression of the 1930s?</p>`,
            marks: 2,
            type: "mcq",
            topic: "Great Depression",
            mcqOptions: [
                { key: "A", text: "The assassination of Archduke Franz Ferdinand" },
                { key: "B", text: "The Wall Street Crash of 1929" },
                { key: "C", text: "The formation of the League of Nations" },
                { key: "D", text: "The Treaty of Versailles signing" },
            ],
        },
        {
            id: "q4",
            questionNumber: "4",
            text: `<p>Describe TWO ways in which Adolf Hitler consolidated his power in Germany between 1933 and 1934.</p>`,
            marks: 8,
            type: "structured",
            topic: "Nazi Germany",
        },
        {
            id: "q5",
            questionNumber: "5",
            text: `<p>Which event marked the beginning of World War II?</p>`,
            marks: 2,
            type: "mcq",
            topic: "World War II",
            mcqOptions: [
                { key: "A", text: "Germany's invasion of Poland on 1 September 1939" },
                { key: "B", text: "Japan's attack on Pearl Harbor in December 1941" },
                { key: "C", text: "Italy's invasion of Ethiopia in 1935" },
                { key: "D", text: "Germany's re-militarization of the Rhineland in 1936" },
            ],
        },
        {
            id: "q6",
            questionNumber: "6",
            text: `<p>Evaluate the impact of the Cold War on developing nations during the period 1945–1991. Use specific examples in your answer.</p>`,
            marks: 6,
            type: "essay",
            topic: "Cold War",
        },
    ],
};

export const getMockPaper = (_id: string): ExamPaper => MOCK_PAPER;
