export interface Rule {
  id: string;
  name: string;
  description?: string;
  condition: string; // A string representing the condition to evaluate, e.g., "exif.Make === 'Canon'"
  action: 'tag' | 'categorize' | 'flag'; // What to do if condition is met
  value?: string; // The tag value, category name, or flag type
}

export interface RuleEvaluationResult {
  ruleId: string;
  ruleName: string;
  passed: boolean;
  actionApplied?: boolean;
  actionValue?: string;
  message?: string;
}
