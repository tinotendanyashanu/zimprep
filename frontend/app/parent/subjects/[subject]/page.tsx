import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { ParentSubjectSummary, ParentSubjectProgressData } from '@/components/parent/ParentSubjectSummary';

interface PageProps {
  params: {
    subject: string;
  };
}

// MOCK DATA GENERATOR
const getSubjectData = (subject: string): ParentSubjectProgressData => {
    const decodedSubject = decodeURIComponent(subject);
    
    return {
        subject: decodedSubject,
        attempts: 12,
        average_score_range: "60-65%",
        average_score_value: 62,
        best_score: 78,
        common_difficulties: [
            "Algebraic expressions involving fractions",
            "Geometric transformation properties",
            "Data interpretation in statistics"
        ]
    };
};

export default function ParentSubjectPage({ params }: PageProps) {
  const data = getSubjectData(params.subject);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
       <main className="flex-1 w-full max-w-4xl mx-auto px-6 py-20">
        
        {/* Breadcrumb / Back Navigation */}
        <Link 
            href="/parent"
            className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-primary transition-colors mb-8"
        >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Overview
        </Link>
        
        {/* Header */}
        <div className="mb-12">
            <h1 className="text-calm-h2 mb-2">
                {data.subject}
            </h1>
            <p className="text-calm-body text-lg">
                Subject Progress Report
            </p>
        </div>

        {/* Content */}
        <ParentSubjectSummary data={data} />

      </main>
    </div>
  );
}
