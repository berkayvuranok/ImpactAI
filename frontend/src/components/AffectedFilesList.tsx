import type { AffectedFile } from "../api/types";

export function AffectedFilesList({ files }: { files: AffectedFile[] }) {
  if (!files.length) {
    return <p className="text-sm text-slate-500">No affected files predicted.</p>;
  }

  return (
    <div className="space-y-2">
      {files.map((file) => (
        <div
          key={file.file_path}
          className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3"
        >
          <div>
            <p className="font-mono text-sm text-white">{file.file_path}</p>
            <p className="text-xs text-slate-500">Rank #{file.rank}</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-brand-400">
              {(file.break_probability * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-slate-500">
              importance {(file.node_importance * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
