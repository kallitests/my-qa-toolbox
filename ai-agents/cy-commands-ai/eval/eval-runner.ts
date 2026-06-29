// Évaluation de cy.aiAssert() sur un jeu de cas étiquetés (eval/dataset.json).
// Objectif : mesurer la fiabilité de l'agent AVANT de le faire confiance en CI —
// c'est ce qui transforme "j'ai branché un LLM" en "j'ai un système mesuré".
//
// Usage: npm run eval

import 'dotenv/config';
import * as fs from 'fs';
import * as path from 'path';
import { runAiAssert } from '../cypress/support/ai/aiAssert';

interface EvalCase {
  html: string;
  intent: string;
  expected: boolean;
}

async function main() {
  const dataset: EvalCase[] = JSON.parse(
    fs.readFileSync(path.join(__dirname, 'dataset.json'), 'utf-8')
  );

  const rows: any[] = [];
  let correct = 0;

  for (const c of dataset) {
    const result = await runAiAssert({ html: c.html, intent: c.intent, url: 'eval://local' });
    const isCorrect = result.pass === c.expected;
    if (isCorrect) correct += 1;
    rows.push({ intent: c.intent, expected: c.expected, predicted: result.pass, correct: isCorrect, reason: result.reason });
  }

  const accuracy = correct / dataset.length;
  const summary = { accuracy, total: dataset.length, correct, rows };

  fs.writeFileSync(path.join(__dirname, 'eval-results.json'), JSON.stringify(summary, null, 2));
  console.table(rows.map(({ reason, ...r }) => r));
  console.log(`\n✅ Accuracy aiAssert: ${(accuracy * 100).toFixed(1)}% (${correct}/${dataset.length})`);

  if (accuracy < 0.75) {
    console.error('❌ Accuracy en dessous du seuil acceptable (75%) — voir eval-results.json');
    process.exit(1);
  }
}

main();
