console.log("Hello from Orca Lab IDE!");

function greet(name) {
  return `Hello, ${name}!`;
}

console.log(greet("Developer"));

// Test some JavaScript features
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
console.log("Doubled:", doubled);

// Async function example
async function fetchExample() {
  console.log("Async functions work!");
  return "Success!";
}

fetchExample().then(result => console.log(result));
