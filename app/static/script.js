// function to display the console output in HTML for debugging
(function() {
    var oldConsoleLog = console.log;
    console.log = function(message) {
        oldConsoleLog(message);
        // Display in HTML
        var consoleOutput = document.getElementById('consoleOutput');
        consoleOutput.innerHTML += message + '<br>';
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    };
})();

// function to display the console output in HTML for debugging
// show by default on page load
window.onload = function() {
    var consoleOutput = document.getElementById('consoleOutput');
    var toggleConsoleCheckbox = document.getElementById('toggleConsole');
    
    // Set the initial visibility of the console based on the checkbox's state
    consoleOutput.style.display = toggleConsoleCheckbox.checked ? 'block' : 'none';
};

// Show the spinner
document.querySelector('.sk-cube-grid').hidden = true;

// Toggle console output
document.getElementById('toggleConsole').addEventListener('change', function() {
    var consoleOutput = document.getElementById('consoleOutput');
    if (this.checked) {
        consoleOutput.style.display = 'block';
    } else {
        consoleOutput.style.display = 'none';
    }
});

// Submit User input form on enter
document.getElementById('inputBox').addEventListener('keypress', function(event) {
    if (event.key === "Enter") { 
        event.preventDefault(); // Prevent the default action to avoid form submission
        document.getElementById('submitButton').click(); // Trigger submit button click
    }
});

function createTableFromJSON(jsonArray) {
    // Check if jsonArray is null, undefined, or empty
    if (!jsonArray || jsonArray.length === 0) {
        console.log("No data available to create table");
        return document.createTextNode("No data available");
    }

    // Create a table element
    let table = document.createElement('table');
    table.style.width = '100%';
    table.setAttribute('border', '1');
    
    // Add column headers
    let colHeaders = Object.keys(jsonArray[0]);
    let thead = table.createTHead();
    let headerRow = thead.insertRow();

    colHeaders.forEach(headerText => {
        let header = document.createElement('th');
        let textNode = document.createTextNode(headerText);
        header.appendChild(textNode);
        headerRow.appendChild(header);
    });

    // Add rows
    let tbody = table.createTBody();
    jsonArray.forEach(row => {
        let trow = tbody.insertRow();
        colHeaders.forEach(column => {
            let cell = trow.insertCell();
            let text = row[column] || '';  // Handle undefined
            cell.appendChild(document.createTextNode(text));
        });
    });

    return table;
}

function createMarkdownTable(jsonArray) {
    let markdown = "";

    // Add column headers
    let colHeaders = Object.keys(jsonArray[0]);
    markdown += colHeaders.join(" | ") + "\n";

    // Separator line
    markdown += colHeaders.map(() => "---").join(" | ") + "\n";

    // Add rows
    jsonArray.forEach(row => {
        let rowData = colHeaders.map(column => row[column] || '').join(" | ");
        markdown += rowData + "\n";
    });

    return markdown;
}

// event listener for transactions button on transactions endpoint
// document.getElementById('initiateButton').addEventListener('click', function() {
//     console.log("Clicked Transactions button");
//     fetch('/transactions')
//     .then(response => response.json())
//     .then(data => {
//         const outputBox = document.getElementById('outputBox');
//         outputBox.innerHTML = ''; // Clear previous content
//         if (Array.isArray(data) && data.length > 0) {
//             const table = createTableFromJSON(data);
//             outputBox.appendChild(table);
//         } else {
//             outputBox.textContent = 'No transaction data available';
//         }
//     })
//     .catch(error => {
//         console.error('Error fetching transactions:', error);
//         document.getElementById('outputBox').textContent = 'Error fetching transactions';
//     });
// }); 

// initiate button and data fetch (transactions.csv or database)
document.getElementById('initiateButton').addEventListener('click', function() {
    console.log("Clicked Initiate button");

     // Show the spinner
    //  document.querySelector('.sk-cube-grid').hidden = false;

    fetch('/initiate')
    .then(response => response.json())
    // format transaction data into table for display in outputBox
    .then(data => {
        if (data.message) {
            // document.querySelector('.sk-cube-grid').hidden = true;
            console.log(data.message);  // Log the message to the console

            // display full output as markdown
            if (data.output) {
                const renderedHtml = marked.parse(data.output); // Convert Markdown to HTML
                document.getElementById('outputBox').innerHTML = renderedHtml; // Display in outputBox
            }
        } else if (data.error) {
            document.querySelector('.sk-cube-grid').hidden = true;
            console.error('Error:', data.error);
            document.getElementById('outputBox').innerHTML = 'Error: ' + data.error;
        }
    })
    .catch(error => {
        document.querySelector('.sk-cube-grid').hidden = true;
        console.error('Error:', error);
        document.getElementById('outputBox').innerHTML = 'Request failed';
    });
});

// Submit box for user input, send to LLM and display output
document.getElementById('submitButton').addEventListener('click', function() {
    console.log("Clicked Submit button");
    var inputText = document.getElementById('inputBox').value;

     // Show the spinner
     document.querySelector('.sk-cube-grid').hidden = false;

    fetch('/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: inputText }),
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector('.sk-cube-grid').hidden = true;
        try {
            console.log("LLM output:");
            const outputData = data.output;
            // console.log(outputData);
            const renderedHtml = marked.parse(data.output); // Convert Markdown to HTML
            document.getElementById('outputBox').innerHTML = renderedHtml;
        } catch (e) {
            console.log(e);
            document.querySelector('.sk-cube-grid').hidden = true;
            document.getElementById('outputBox').value = data.output;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Stop the spinner in case of an error as well
        document.querySelector('.sk-cube-grid').hidden = true;
    });
});

// Close OpenAI connection
document.getElementById('closeButton').addEventListener('click', function() {
    console.log("Clicked Close button");
    fetch('/close')
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            console.log(data.message);
            // Update the UI or notify the user as needed
        } else if (data.error) {
            console.error('Error:', data.error);
            // Handle errors
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Handle network errors
    });
});

// Fetch and display accounts in debug panel in UI
function fetchAndDisplayAccounts() {
    fetch('/fetch_accounts')
    .then(response => response.json())
    .then(data => {
        // Assuming 'data' is an array of account objects
        let output = '<h3>Account Data</h3><div>';
        data.forEach(account => {
            output += '<div>' + JSON.stringify(account) + '</div>';
        });
        output += '</div>';

        document.getElementById('consoleOutput').innerHTML = output;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
