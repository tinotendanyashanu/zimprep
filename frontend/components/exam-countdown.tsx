/**
 * Exam Countdown Timer Component
 *
 * Displays real-time countdown to upcoming exams with urgency-based styling.
 * Updates every minute for exams more than 24 hours away, every second for imminent exams.
 */

import { useEffect, useState } from "react";

interface ExamCountdownProps {
  scheduledDate: {
    utc: string;
    local: string;
    timezone: string;
    display: string;
  };
  examName: string;
  subject: string;
  paper: string;
  className?: string;
}

type UrgencyLevel = "low" | "medium" | "high" | "critical" | "passed";

interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  totalSeconds: number;
  urgency: UrgencyLevel;
  display: string;
}

export function ExamCountdown({
  scheduledDate,
  examName,
  subject,
  paper,
  className = "",
}: ExamCountdownProps) {
  const [timeRemaining, setTimeRemaining] = useState<TimeRemaining | null>(
    null,
  );

  useEffect(() => {
    function calculateTimeRemaining(): TimeRemaining {
      const now = new Date();
      const examTime = new Date(scheduledDate.local);
      const diffMs = examTime.getTime() - now.getTime();

      if (diffMs <= 0) {
        return {
          days: 0,
          hours: 0,
          minutes: 0,
          seconds: 0,
          totalSeconds: 0,
          urgency: "passed",
          display: "Exam has started or passed",
        };
      }

      const totalSeconds = Math.floor(diffMs / 1000);
      const days = Math.floor(totalSeconds / (24 * 3600));
      const hours = Math.floor((totalSeconds % (24 * 3600)) / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;

      // Determine urgency
      let urgency: UrgencyLevel;
      if (totalSeconds < 3600) {
        urgency = "critical"; // Less than 1 hour
      } else if (totalSeconds < 86400) {
        urgency = "high"; // Less than 1 day
      } else if (totalSeconds < 259200) {
        urgency = "medium"; // Less than 3 days
      } else {
        urgency = "low";
      }

      // Format display
      let display: string;
      if (days > 0) {
        display = `${days} day${days !== 1 ? "s" : ""}, ${hours} hour${hours !== 1 ? "s" : ""}`;
      } else if (hours > 0) {
        display = `${hours} hour${hours !== 1 ? "s" : ""}, ${minutes} min${minutes !== 1 ? "s" : ""}`;
      } else if (minutes > 0) {
        display = `${minutes} minute${minutes !== 1 ? "s" : ""}`;
      } else {
        display = `${seconds} second${seconds !== 1 ? "s" : ""}`;
      }

      return {
        days,
        hours,
        minutes,
        seconds,
        totalSeconds,
        urgency,
        display,
      };
    }

    // Initial calculation
    setTimeRemaining(calculateTimeRemaining());

    // Update interval based on urgency
    const time = calculateTimeRemaining();
    const updateInterval = time.urgency === "critical" ? 1000 : 60000; // 1s for critical, 1min for others

    const interval = setInterval(() => {
      setTimeRemaining(calculateTimeRemaining());
    }, updateInterval);

    return () => clearInterval(interval);
  }, [scheduledDate.local]);

  if (!timeRemaining) {
    return null;
  }

  // Urgency-based styling
  const urgencyColors = {
    low: "text-green-600 dark:text-green-400",
    medium: "text-yellow-600 dark:text-yellow-400",
    high: "text-orange-600 dark:text-orange-400",
    critical: "text-red-600 dark:text-red-400 font-bold animate-pulse",
    passed: "text-gray-500 dark:text-gray-400",
  };

  const urgencyBgColors = {
    low: "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800",
    medium:
      "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800",
    high: "bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800",
    critical: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
    passed:
      "bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800",
  };

  const urgencyIcon = {
    low: "📅",
    medium: "⏰",
    high: "⚠️",
    critical: "🚨",
    passed: "✅",
  };

  return (
    <div
      className={`
        exam-countdown 
        p-4 rounded-lg border-2 
        ${urgencyBgColors[timeRemaining.urgency]}
        transition-all duration-300
        ${className}
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">
              {urgencyIcon[timeRemaining.urgency]}
            </span>
            <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100">
              {subject} - {paper}
            </h3>
          </div>

          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            {scheduledDate.display}
          </div>

          <div
            className={`text-xl font-mono ${urgencyColors[timeRemaining.urgency]}`}
          >
            {timeRemaining.display}
          </div>

          {timeRemaining.urgency === "critical" && (
            <div className="mt-2 text-sm font-medium text-red-600 dark:text-red-400">
              Exam starting soon!
            </div>
          )}
        </div>

        {/* Visual urgency indicator */}
        <div className="flex flex-col items-center gap-1 ml-4">
          <div
            className={`
            w-3 h-3 rounded-full 
            ${
              timeRemaining.urgency === "critical"
                ? "bg-red-500 animate-pulse"
                : timeRemaining.urgency === "high"
                  ? "bg-orange-500"
                  : timeRemaining.urgency === "medium"
                    ? "bg-yellow-500"
                    : timeRemaining.urgency === "low"
                      ? "bg-green-500"
                      : "bg-gray-400"
            }
          `}
          />
          <span className="text-xs text-gray-500 capitalize">
            {timeRemaining.urgency}
          </span>
        </div>
      </div>

      {/* Detailed breakdown for exams >1 day away */}
      {timeRemaining.days > 0 && timeRemaining.urgency !== "critical" && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-4 gap-2 text-center text-sm">
            <div>
              <div className="font-bold text-gray-900 dark:text-gray-100">
                {timeRemaining.days}
              </div>
              <div className="text-xs text-gray-500">days</div>
            </div>
            <div>
              <div className="font-bold text-gray-900 dark:text-gray-100">
                {timeRemaining.hours}
              </div>
              <div className="text-xs text-gray-500">hours</div>
            </div>
            <div>
              <div className="font-bold text-gray-900 dark:text-gray-100">
                {timeRemaining.minutes}
              </div>
              <div className="text-xs text-gray-500">mins</div>
            </div>
            <div>
              <div className="font-bold text-gray-900 dark:text-gray-100">
                {timeRemaining.seconds}
              </div>
              <div className="text-xs text-gray-500">secs</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Usage example:
/*
import { ExamCountdown } from '@/components/exam-countdown'

function UpcomingExams({ exams }) {
  return (
    <div className="space-y-4">
      {exams.map(exam => (
        <ExamCountdown
          key={exam.exam_id}
          scheduledDate={exam.scheduled_date}
          examName={`${exam.subject} ${exam.paper}`}
          subject={exam.subject}
          paper={exam.paper}
        />
      ))}
    </div>
  )
}
*/
