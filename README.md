# **SEMTUI: Semantic Enrichment of Tabular Data**

**Version:** 0.1.1  
**Author:** Alidu Abubakari  
**Email:** [a.abubakari@campus.unimib.it](mailto:a.abubakari@campus.unimib.it)  
**Repository:** [SEMTUI GitHub Repository](https://github.com/aliduabubakari/semtui1.1.git)

---

## **Overview**

**SEMTUI** is a Python library designed for the semantic enrichment of tabular data. It facilitates the transformation, modification, and enhancement of tables with additional semantic information. The package is modular, making it adaptable for both expert users and non-experts, offering an intuitive approach to complex data enrichment tasks.

With this package, users can extend their tables with external data, reconcile values against external sources, and evaluate data quality, ensuring that the enriched datasets are accurate and valuable for downstream analysis.

---

## **SemTUI Python Library Structure**

```
semtui_refactored
│
├── __init__.py
├── data_handler.py
├── data_modifier.py
├── dataset_manager.py
├── extension_manager.py
├── main.py
├── reconciliation_manager.py
├── semtui_evals.py
├── token_manager.py
├── utils.py
│
├── setup.py
├── LICENSE
├── README.md
```

## **Explanation of Main Functions:**

1. **Root Directory (`semtui_refactored`)**: Contains core library files.
   - `__init__.py`: Initializes the package when imported.
   - `data_handler.py`: Manages data input/output and processing.
   - `data_modifier.py`: Handles modification and enrichment of data.
   - `dataset_manager.py`: Manages dataset operations like loading and merging.
   - `extension_manager.py`: Controls the addition of extensions or plugins to expand library functionalities.
   - `main.py`: The primary entry point for the library; orchestrates key tasks.
   - `reconciliation_manager.py`: Manages the reconciliation of data with external sources.
   - `semtui_evals.py`: Provides evaluation tools or metrics to assess data enrichment.
   - `token_manager.py`: Handles authentication tokens for communication with external services.
   - `utils.py`: Contains utility functions that assist the core functionality.

---

## **Key Features**

- **Modular Structure:** Adaptable for various data enrichment workflows.
- **Semantic Enrichment:** Add meaningful semantic context to tabular data.
- **Reconciliation:** Match table data with external sources for verification.
- **Dataset Management:** Efficient handling and modification of large datasets.
- **Extensions:** Seamlessly integrate additional features through extensions.
- **Evaluation:** Assess the quality of enriched datasets.
- **Ease of Use:** Intuitive for both experts and non-experts.

---

## **Installation**

To install **SEMTUI** locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aliduabubakari/semtui1.1.git
   ```

2. **Navigate to the cloned directory**:
   ```bash
   cd semtui1.1
   ```

3. **Create and activate a virtual environment** (optional but recommended):
   - For macOS/Linux:
     ```bash
     python3 -m venv myenv
     source myenv/bin/activate
     ```
   - For Windows:
     ```bash
     python -m venv myenv
     myenv\Scripts\activate
     ```

4. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install the library**:
   ```bash
   pip install .
   ```
---

### Installing the SemTUI Python Library

- **Create a Python Virtual Environment**
  - Run: `python3 -m venv myenv`

- **Activate the Virtual Environment**
  - **For macOS and Linux:**
    - Run: `source myenv/bin/activate`
  - **For Windows:**
    - Run: `myenv\Scripts\activate`

- **Install the SemTUI Python Library**
  - Run: `pip install --upgrade git+https://github.com/aliduabubakari/semtui1.1.git`

- **Explore the Sample Notebook**
  - **Launch Jupyter Notebook:**
    - Run: `jupyter notebook`
  - **Open the Sample Notebook:**
    - Locate and open `sample_notebook.ipynb` from the Jupyter interface.
  - **Run and Review:**
    - Execute the cells to see example implementations.

- **Note**
  - Ensure Git is installed on your system since the library is fetched from a GitHub repository.

---

By following these bullet-pointed steps, you can quickly set up and start using the SemTUI Python library for semantic enrichment of your tabular data.

## **Dependencies**

**SEMTUI** relies on the following Python libraries:

- **pandas** - for efficient data handling and manipulation.
- **numpy** - for numerical computations.
- **chardet** - for character encoding detection.
- **PyJWT** - for secure token handling and authentication.
- **fake-useragent** - to generate random user agents for web scraping.
- **requests** - for making HTTP requests to external APIs.

All dependencies are automatically installed when using `pip`.

---

## **Usage**

Here’s a quick start guide to using **SEMTUI**:

### **Basic Example**

```python
from semtui_refactored import dataset_manager, data_modifier, reconciliation_manager

# Load a dataset
dataset = dataset_manager.load_dataset('path_to_dataset.csv')

# Modify the dataset by applying enrichment
modified_dataset = data_modifier.modify_data(dataset)

# Reconcile values from an external source
reconciled_data = reconciliation_manager.reconcile_data(modified_dataset)

# Save the enriched and reconciled dataset
dataset_manager.save_dataset(reconciled_data, 'enriched_dataset.csv')
```

### **Main Components**

The library consists of several key components:

1. **`data_handler.py`:** Manages data input and output, ensures efficient loading and saving of datasets.
2. **`data_modifier.py`:** Applies modifications and semantic enrichments to datasets.
3. **`dataset_manager.py`:** Handles dataset operations such as loading, saving, and merging data.
4. **`extension_manager.py`:** Allows for extending functionalities of the library with custom extensions.
5. **`reconciliation_manager.py`:** Performs reconciliation, matching table data with external sources for validation.
6. **`semtui_evals.py`:** Provides tools for evaluating the quality and accuracy of enriched data.
7. **`token_manager.py`:** Manages authentication tokens for secure interaction with external APIs.
8. **`utils.py`:** A collection of utility functions to support core functionalities.

---

## **How It Works**

The **SEMTUI** library works by allowing users to load tabular data, modify it with external semantic information, reconcile it with external data sources, and evaluate the final dataset.

### **Workflow:**
1. **Load Data**: Load raw tabular data from a CSV or other supported formats.
2. **Modify Data**: Apply transformations and add semantic information from external sources.
3. **Reconcile Data**: Match and validate table data with authoritative external sources (e.g., APIs).
4. **Evaluate Data**: Ensure the enriched data is accurate and of high quality.
5. **Save Data**: Export the final, enriched dataset for further use or analysis.

---

## **Extending SEMTUI**

**SEMTUI** is designed to be modular and extensible. You can add custom functionalities by writing extensions. Use the `extension_manager.py` to integrate your custom modules into the pipeline without modifying the core code.

---

## **Example Notebooks**

To help you get started, **SEMTUI** comes with example Jupyter notebooks that showcase its functionalities. Open and run these notebooks to see how to implement various tasks such as data loading, enrichment, reconciliation, and evaluation.

```bash
jupyter notebook SEMTUI_Explanation.ipynb
```

---

## **Development**

Feel free to contribute to the project by forking the repository and submitting a pull request. 

### **Setting Up for Development**
1. **Fork the repository** on GitHub.
2. **Clone your forked repository**:
   ```bash
   git clone https://github.com/yourusername/semtui1.1.git
   ```
3. **Install development dependencies**:
   ```bash
   pip install -r dev-requirements.txt
   ```

---

## **License**

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more information.

---

## **Contact**

For any questions, suggestions, or feedback, feel free to reach out to the author:

- **Alidu Abubakari**
- [a.alidu@campus.unimib.it](mailto:a.alidu@campus.unimib.it)

---

### **Acknowledgments**
- Special thanks to the open-source community for providing essential libraries that power this project.

---
