import ms from "ms";
import { version } from "ms/package.json";

export function greet() {
  console.log(`hello from lib, one minute is ${ms(60_000)} (ms ${version})`);
}
