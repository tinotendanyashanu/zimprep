"use client";

import { createContext, useContext } from "react";

export type StudentProfile = {
  id: string;
  name: string;
  examBoard: string;   // 'zimsec' | 'cambridge'
  level: string;       // 'Grade7' | 'O' | 'A' | 'IGCSE' | 'AS_Level' | 'A_Level'
};

export const StudentContext = createContext<StudentProfile | null>(null);

export function useStudent(): StudentProfile {
  const ctx = useContext(StudentContext);
  if (!ctx) throw new Error("useStudent must be used inside StudentLayout");
  return ctx;
}
