import { EmptyState } from "@/components/system/EmptyState";
import Link from "next/link";
import { FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <EmptyState
          icon={FileQuestion}
          title="Page Not Found"
          description="The page you are looking for does not exist or has been moved."
        />
        <div className="mt-6 flex justify-center">
          <Button asChild variant="default">
            <Link href="/dashboard">Return Home</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
