import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { DynamicToolUIPart, ToolUIPart } from "ai";
import { cn } from "@/lib/utils";
import { Wrench, Loader2, Check, AlertCircle } from "lucide-react";

// Helper function to get state information
function getStateInfo(state: string) {
  switch (state) {
    case "input-streaming":
      return {
        icon: Wrench,
        label: "Using ",
        color: "text-muted-foreground",
      };
    case "input-available":
      return {
        icon: Loader2,
        label: "Using ",
        color: "text-muted-foreground",
      };
    case "output-available":
      return {
        icon: Check,
        label: "Used ",
        color: "text-success",
      };
    case "output-error":
      return {
        icon: AlertCircle,
        label: "Failed to use",
        color: "text-destructive",
      };
    default:
      return {
        icon: Wrench,
        label: "Using",
        color: "text-muted-foreground",
      };
  }
}

// Helper function to safely render unknown values
function renderValue(value: unknown): React.ReactNode {
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

export default function ChatTool({
  toolMessagePart,
  className,
}: {
  toolMessagePart: ToolUIPart | DynamicToolUIPart;
  className?: string;
}) {
  const toolName =
    toolMessagePart.type === "dynamic-tool"
      ? toolMessagePart.toolName
      : toolMessagePart.type.replace("tool-", "");

  const stateInfo = getStateInfo(toolMessagePart.state);
  const StateIcon = stateInfo.icon;

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem
        value="tool"
        className={cn(
          "px-2 border rounded-xl hover:no-underline py-2 w-full last:border-b shadow-xs",
          className
        )}
      >
        <AccordionTrigger className={cn("py-0 hover:no-underline hover:opacity-70 transition-all")}>
          <span className="flex items-center gap-2">
            <StateIcon
              className={cn(
                "w-4 h-4",
                stateInfo.color,
                toolMessagePart.state === "input-available" && "animate-spin"
              )}
            />
            <span className="text-sm">
              {stateInfo.label} {toolName}
            </span>
          </span>
        </AccordionTrigger>
        <AccordionContent className="pb-0">
          <div className="flex flex-col gap-3 w-full pt-2">
            {/* Error Section - show for failed executions */}
            {toolMessagePart.state === "output-error" && toolMessagePart.errorText && (
              <div className="bg-destructive/5 border rounded-md p-2 text-sm overflow-x-auto whitespace-pre-wrap text-destructive w-full">
                {toolMessagePart.errorText}
              </div>
            )}
            {/* Input Section - always show if available */}
            {"input" in toolMessagePart &&
            toolMessagePart.input !== undefined &&
            toolMessagePart.input !== null ? (
              <div className="w-full">
                <div className="text-xs font-semibold text-muted-foreground mb-1">Input</div>
                <pre className="bg-muted rounded-md p-2 text-sm overflow-x-auto whitespace-pre-wrap w-full">
                  {renderValue(toolMessagePart.input)}
                </pre>
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">No input</div>
            )}

            {/* Output Section - show for successful completion */}
            {toolMessagePart.state === "output-available" &&
              "output" in toolMessagePart &&
              toolMessagePart.output !== undefined &&
              toolMessagePart.output !== null && (
                <div className="w-full">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">Output</div>
                  <pre className="bg-muted rounded-md p-2 text-sm overflow-x-auto whitespace-pre-wrap w-full">
                    {renderValue(toolMessagePart.output)}
                  </pre>
                </div>
              )}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
