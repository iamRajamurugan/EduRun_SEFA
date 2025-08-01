console.log("JavaScript Runtime Error Example");
console.log("This will demonstrate various runtime errors");

// This will cause a ReferenceError
console.log("Trying to access undefined variable:");
console.log(undefinedVariable);  // ReferenceError

// This line won't be reached due to the error above
console.log("This line should not be executed");

// More potential runtime errors (won't be reached):
const obj = null;
console.log(obj.property);  // TypeError

const func = undefined;
func();  // TypeError
