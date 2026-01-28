# StageFlow Inference Code Description

This folder contains Python example codes for inference using the StageFlow framework, as demonstrated in the paper. 
It utilizes the CoSQL and Sparc testsets and their database for its operations. 
😉 Please ensure you download the CoSQL dataset from [CoSQL](https://yale-lily.github.io/cosql) 
and place it in the `datasets` folder before running the code. 
Below is a brief description of each `.py` file:

- **predict_complex.py**  
    Complete inference code, including all functionalities such as question type recognition and complex reasoning.

- **predict_IS_complex.py**  
    Inference code without question type recognition functionality, focusing on complex reasoning.

- **predict.py**  
    Standard inference code for general reasoning tasks.

- **predict_zeroshot.py**  
    Zero-shot inference code for open-source general reasoning tasks.

- **predict_zeroshot_complete_missing_items.py**  
    Zero-shot inference code for open-source general reasoning tasks, with the ability to complete missing items.

- **predict_zeroshot_SQLonly.py**  
    Zero-shot inference code for open-source general reasoning tasks(especially for Sparc testset).

- **predict_zeroshot_SQLonly_complete_missing_items.py**  
    Zero-shot inference code for open-source general reasoning tasks(especially for Sparc testset), with the ability to complete missing items.

To evaluate the output files, please use the `evaluate.py` script in `/evaluation` folder.
