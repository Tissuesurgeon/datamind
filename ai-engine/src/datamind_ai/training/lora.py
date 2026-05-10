"""LoRA fine-tuning runner.

This is a real implementation (PEFT + TRL) but only activates when explicitly
opted-in via env var `AI_LORA_REAL=1`. By default we stream simulated metrics
so the demo never waits on a multi-minute training run.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from datamind_ai.training.config import TrainingConfig


def real_train_supported() -> bool:
    return os.environ.get("AI_LORA_REAL", "0") == "1"


def lora_train(cfg: TrainingConfig, dataset_text: str) -> Iterator[dict]:  # pragma: no cover
    """Yield progress events while running a real LoRA fine-tune.

    NOTE: This path requires GPU + downloads weights. Default DataMind demos
    stay in simulated mode (`simulate_training_stream`). The implementation is
    written here for completeness so production deploys can flip a single flag.
    """
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainerCallback,
            TrainingArguments,
        )
    except Exception as exc:
        yield {"step": 0, "epoch": 0, "loss": 0.0, "message": f"deps missing: {exc}"}
        return

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    )
    peft_cfg = LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        target_modules="all-linear",
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_cfg)

    lines = [l for l in dataset_text.splitlines() if l.strip()][:5000]
    ds = Dataset.from_dict({"text": lines or ["sample text for demo training"]})

    def tok(examples):
        out = tokenizer(
            examples["text"], truncation=True, max_length=cfg.max_seq_length, padding="max_length"
        )
        out["labels"] = out["input_ids"].copy()
        return out

    ds = ds.map(tok, batched=True, remove_columns=ds.column_names)

    events: list[dict] = []

    class StreamCB(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):  # noqa: D401
            if logs:
                events.append(
                    {
                        "step": state.global_step,
                        "epoch": float(state.epoch or 0),
                        "loss": float(logs.get("loss", 0.0)),
                        "learning_rate": float(logs.get("learning_rate", cfg.learning_rate)),
                    }
                )

    args = TrainingArguments(
        output_dir=f"./checkpoints/{cfg.job_id}",
        num_train_epochs=cfg.epochs,
        per_device_train_batch_size=cfg.batch_size,
        learning_rate=cfg.learning_rate,
        logging_steps=2,
        save_strategy="no",
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        callbacks=[StreamCB()],
    )
    trainer.train()
    for evt in events:
        yield evt
