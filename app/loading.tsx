import { LoadingState } from "@/components/system/LoadingState";

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <LoadingState variant="spinner" text="Loading ZimPrep..." />
    </div>
  );
}
