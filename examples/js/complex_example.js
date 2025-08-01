// JavaScript Complex Example - Async/Await and Modern Features
console.log("JavaScript Complex Example - Modern Features Demo");
console.log("=".repeat(50));

// Class definition
class DataProcessor {
    constructor(name) {
        this.name = name;
        this.data = [];
    }
    
    addData(items) {
        this.data.push(...items);
        return this;
    }
    
    process() {
        return this.data
            .filter(x => x > 0)
            .map(x => x * 2)
            .reduce((sum, x) => sum + x, 0);
    }
    
    async asyncProcess() {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(this.process());
            }, 100);
        });
    }
}

// Async function demo
async function demonstrateAsync() {
    console.log("🔄 Starting async operations...");
    
    const processor = new DataProcessor("Demo Processor");
    processor.addData([1, -2, 3, 4, -5, 6]);
    
    console.log(`Raw data: [${processor.data.join(", ")}]`);
    
    // Sync processing
    const syncResult = processor.process();
    console.log(`Sync result: ${syncResult}`);
    
    // Async processing
    const asyncResult = await processor.asyncProcess();
    console.log(`Async result: ${asyncResult}`);
    
    return { sync: syncResult, async: asyncResult };
}

// Modern JavaScript features
const modernFeatures = () => {
    console.log("\n🚀 Modern JavaScript Features:");
    
    // Destructuring
    const obj = { a: 1, b: 2, c: 3 };
    const { a, b, ...rest } = obj;
    console.log(`Destructured: a=${a}, b=${b}, rest=${JSON.stringify(rest)}`);
    
    // Template literals
    const name = "JavaScript";
    const version = "ES2023";
    console.log(`Running ${name} ${version} in Docker!`);
    
    // Arrow functions and array methods
    const numbers = [1, 2, 3, 4, 5];
    const doubled = numbers.map(x => x * 2);
    const sum = doubled.reduce((acc, x) => acc + x, 0);
    console.log(`Original: [${numbers}] → Doubled: [${doubled}] → Sum: ${sum}`);
};

// Main execution
async function main() {
    try {
        modernFeatures();
        
        console.log("\n⏰ Executing async demo...");
        const results = await demonstrateAsync();
        
        console.log("\n✅ JavaScript complex example completed successfully!");
        console.log(`Final results: ${JSON.stringify(results, null, 2)}`);
        
    } catch (error) {
        console.error("❌ Error:", error.message);
    }
}

// Run the main function
main();
