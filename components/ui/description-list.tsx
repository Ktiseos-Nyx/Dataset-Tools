import * as React from "react";
import { cn } from "@/lib/utils";

export interface DescriptionListProps extends React.HTMLAttributes<HTMLDListElement> {
  data: Record<string, React.ReactNode | string | number>;
  layout?: "default" | "stacked";
}

const DescriptionList = React.forwardRef<HTMLDListElement, DescriptionListProps>(
  ({ className, data, layout = "default", ...props }, ref) => {
    const entries = Object.entries(data);

    return (
      <dl
        ref={ref}
        className={cn("divide-y divide-border rounded-lg w-full", className)}
        {...props}
      >
        {entries.map(([key, value], index) => {
          if (layout === "stacked") {
            return (
              <div
                key={index}
                className="flex flex-col gap-0 px-4 py-4 transition-all duration-150 ease-out hover:duration-75 hover:rounded-md hover:bg-muted"
              >
                <dt className="font-medium text-sm capitalize text-muted-foreground">{key}</dt>
                <dd className="">{value}</dd>
              </div>
            );
          }

          return (
            <div
              key={index}
              className="grid grid-cols-3 items-start justify-items-start px-4 py-4 transition-all duration-150 ease-out hover:duration-75 hover:rounded-md hover:bg-muted"
            >
              <dt className="font-medium capitalize">{key}</dt>
              <dd className="col-span-2 text-muted-foreground">{value}</dd>
            </div>
          );
        })}
      </dl>
    );
  }
);
DescriptionList.displayName = "DescriptionList";

export { DescriptionList };
