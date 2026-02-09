import { NextResponse } from 'next/server';
import type { ImageMetadata } from '@/types/metadata';
import type { Rule, RuleEvaluationResult } from '@/types/rules';

export async function POST(request: Request) {
  try {
    const { rules, metadata }: { rules: Rule[]; metadata: ImageMetadata } = await request.json();

    if (!rules || !Array.isArray(rules) || !metadata) {
      return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
    }

    const results: RuleEvaluationResult[] = [];

    for (const rule of rules) {
      let passed = false;
      let message = 'Rule not evaluated';

      // Very basic evaluation logic for now - this will be replaced by a proper rule engine
      if (rule.condition.startsWith('exif.Make ===')) {
        const expectedMake = rule.condition.split("===")[1].trim().replace(/'/g, '');
        if (metadata.exif && metadata.exif.Make === expectedMake) {
          passed = true;
          message = `EXIF Make matches '${expectedMake}'`;
        } else {
          message = `EXIF Make does not match '${expectedMake}' or is not present`;
        }
      } else {
        message = 'Unsupported rule condition type';
      }

      results.push({
        ruleId: rule.id,
        ruleName: rule.name,
        passed,
        actionApplied: passed, // For now, action is applied if passed
        actionValue: rule.value,
        message,
      });
    }

    return NextResponse.json(results);
  } catch (error) {
    if (error instanceof Error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'An unknown error occurred' }, { status: 500 });
  }
}
