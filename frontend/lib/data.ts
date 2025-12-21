export const SUBJECTS_DB = [
  "Mathematics", "English Language", "Shona", "Ndebele", 
  "Physics", "Chemistry", "Biology", "Combined Science", 
  "History", "Geography", "Commerce", "Principles of Accounts", 
  "Computer Science", "Literature in English", "Agriculture", 
  "Business Studies", "Economics", "Sociology", "Divinity"
];

export interface Paper {
  id: string;
  name: string;
  type: "Multiple Choice" | "Structured" | "Practical" | "Essay";
  duration: string; // e.g., "2 hours 30 mins"
  description: string;
}

export const MOCK_PAPERS: Record<string, Paper[]> = {
  default: [
    {
      id: "paper-1",
      name: "Paper 1",
      type: "Multiple Choice",
      duration: "1 hour 30 mins",
      description: "Standard multiple choice paper covering the core syllabus."
    },
    {
      id: "paper-2",
      name: "Paper 2",
      type: "Structured",
      duration: "2 hours 30 mins",
      description: "Structured questions requiring detailed working and explanations."
    }
  ],
  "Mathematics": [
    {
       id: "paper-1",
       name: "Paper 1",
       type: "Multiple Choice",
       duration: "2 hours 30 mins",
       description: "Non-calculator paper covering fundamental mathematical concepts."
    },
    {
       id: "paper-2",
       name: "Paper 2",
       type: "Structured",
       duration: "2 hours 30 mins",
       description: "Calculator-allowed paper with more complex structured problems."
    }
  ],
   "English Language": [
    {
       id: "paper-1",
       name: "Paper 1",
       type: "Essay",
       duration: "1 hour 30 mins",
       description: "Free composition and guided composition."
    },
    {
       id: "paper-2",
       name: "Paper 2",
       type: "Structured",
       duration: "2 hours",
       description: "Comprehension, summary and supporting language structures."
    }
  ],
  "Combined Science": [
      {
          id: "paper-1",
          name: "Paper 1",
          type: "Multiple Choice",
          duration: "1 hour",
          description: "Multiple choice questions covering Physics, Chemistry and Biology sections."
      },
      {
          id: "paper-2",
          name: "Paper 2",
          type: "Structured",
          duration: "2 hours",
          description: "Theory questions from all three science disciplines."
      },
      {
          id: "paper-3",
          name: "Paper 3",
          type: "Practical",
          duration: "1 hour 30 mins",
          description: "Practical assessment or alternative to practical."
      }
  ]
};

export function getPapersForSubject(subject: string): Paper[] {
  return MOCK_PAPERS[subject] || MOCK_PAPERS["default"];
}
