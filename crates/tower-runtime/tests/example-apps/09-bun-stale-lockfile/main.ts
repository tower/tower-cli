import ms from "ms";

console.log(`One minute is ${ms(60_000)}`);
console.log(`The greeting is: ${process.env.GREETING ?? "unset"}`);
console.log(`The parent variable is: ${process.env.BUN_TEST_PARENT_VARIABLE ?? "unset"}`);
