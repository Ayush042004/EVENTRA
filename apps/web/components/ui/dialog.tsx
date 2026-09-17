import React from "react";

export function Dialog({ children, open }: { children?: React.ReactNode; open?: boolean }) {
  if (!open) return null;
  return <div role="dialog">{children}</div>;
}
