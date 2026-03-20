import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { QuestionFeedback } from "@/lib/results/types";
import { CheckCircle2, AlertCircle, XCircle, BookOpen } from "lucide-react";

interface QuestionFeedbackItemProps {
  data: QuestionFeedback;
}

export function QuestionFeedbackItem({ data }: QuestionFeedbackItemProps) {
  const getStatusConfig = (status: QuestionFeedback["status"]) => {
    switch (status) {
      case "full":
        return { icon: CheckCircle2, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" };
      case "partial":
        return { icon: AlertCircle, color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" };
      case "zero":
        return { icon: XCircle, color: "text-red-600", bg: "bg-red-50", border: "border-red-200" };
      default:
        return { icon: AlertCircle, color: "text-zinc-400", bg: "bg-zinc-50", border: "border-zinc-200" };
    }
  };

  const statusConfig = getStatusConfig(data.status);
  const StatusIcon = statusConfig.icon;

  return (
    <AccordionItem value={data.id} className="border border-zinc-200 bg-white rounded-lg mb-4 overflow-hidden shadow-sm">
      <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-zinc-50 transition-colors">
        <div className="flex items-center justify-between w-full pr-4">
          <div className="flex items-center gap-4">
            <div className={`w-8 h-8 rounded-md flex items-center justify-center font-bold text-sm border ${statusConfig.bg} ${statusConfig.border} ${statusConfig.color}`}>
              {data.questionNumber}
            </div>
            <div className="text-left">
              <div className="font-medium text-zinc-900">Question {data.questionNumber}</div>
              <div className="text-xs text-zinc-500">{data.topic}</div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-right">
            <div className="text-sm font-medium text-zinc-900 border px-2 py-0.5 rounded border-zinc-200 bg-zinc-50">
              {data.awardedMarks} <span className="text-zinc-400">/</span> {data.totalMarks}
            </div>
            <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
          </div>
        </div>
      </AccordionTrigger>

      <AccordionContent className="px-0 pb-0">
        <div className="border-t border-zinc-100">
          {/* Student Answer */}
          <div className="p-6 bg-zinc-50/50 border-b border-zinc-100">
            <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Your Answer</h4>
            <div className="font-mono text-sm text-zinc-700 bg-white p-3 border border-zinc-200 rounded whitespace-pre-wrap">
              {data.studentAnswer || <span className="italic text-zinc-400">No answer provided</span>}
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Feedback Summary */}
            <div>
              <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-zinc-900 inline-block" />
                Examiner Feedback
              </h4>
              <p className="text-sm text-zinc-600 leading-relaxed max-w-prose">
                {data.examinerFeedback}
              </p>
            </div>

            {/* Correct Points */}
            {data.correct_points && data.correct_points.length > 0 && (
              <div className="bg-emerald-50/50 border border-emerald-100 rounded-md p-4">
                <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">Marks Awarded For</h4>
                <ul className="space-y-2">
                  {data.correct_points.map((point, idx) => (
                    <li key={idx} className="text-sm text-emerald-700 flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-500" />
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Points */}
            {data.missingPoints && data.missingPoints.length > 0 && (
              <div className="bg-red-50/50 border border-red-100 rounded-md p-4">
                <h4 className="text-xs font-bold text-red-800 uppercase tracking-wider mb-2">Marks Deducted For</h4>
                <ul className="space-y-2">
                  {data.missingPoints.map((point, idx) => (
                    <li key={idx} className="text-sm text-red-700 flex items-start gap-2">
                      <span className="block w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Study References */}
            {data.study_references && data.study_references.length > 0 && (
              <div className="bg-blue-50/50 border border-blue-100 rounded-md p-4">
                <h4 className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <BookOpen className="w-3.5 h-3.5" /> Revision Resources
                </h4>
                <ul className="space-y-1">
                  {data.study_references.map((ref, idx) => (
                    <li key={idx} className="text-sm text-blue-700 flex items-start gap-2">
                      <span className="block w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                      {ref}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </AccordionContent>
    </AccordionItem>
  );
}
