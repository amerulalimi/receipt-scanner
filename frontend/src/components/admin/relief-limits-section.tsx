"use client";

import { startTransition, useActionState, useState } from "react";

import {
  createReliefLimitAction,
  deactivateReliefLimitAction,
  updateReliefLimitAction,
} from "@/actions/admin-system";
import type { AdminActionState } from "@/actions/admin-config";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getCategoryLabel } from "@/lib/constants/receipts";
import { formatRinggit } from "@/lib/receipt-format";
import type { ReliefLimitItem } from "@/lib/api/types";

const initialState: AdminActionState = {};

export function ReliefLimitsSection({
  limits,
}: {
  limits: ReliefLimitItem[];
}) {
  const [createState, createAction, isCreating] = useActionState(
    createReliefLimitAction,
    initialState,
  );
  const [updateState, updateAction, isUpdating] = useActionState(
    updateReliefLimitAction,
    initialState,
  );
  const [deactivateState, deactivateAction, isDeactivating] = useActionState(
    deactivateReliefLimitAction,
    initialState,
  );

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [draftCategory, setDraftCategory] = useState("");
  const [draftAmount, setDraftAmount] = useState("");
  const [draftDescription, setDraftDescription] = useState("");
  const [draftBeSeksyen, setDraftBeSeksyen] = useState("");
  const [draftSortOrder, setDraftSortOrder] = useState("");
  const [draftIsActive, setDraftIsActive] = useState(true);

  const [newCategory, setNewCategory] = useState("");
  const [newAmount, setNewAmount] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newBeSeksyen, setNewBeSeksyen] = useState("");
  const [newSortOrder, setNewSortOrder] = useState("");

  const feedback =
    createState.error ||
    updateState.error ||
    deactivateState.error ||
    (createState.success ? createState.message : null) ||
    (updateState.success ? updateState.message : null) ||
    (deactivateState.success ? deactivateState.message : null);

  const isPending = isCreating || isUpdating || isDeactivating;

  function startEdit(item: ReliefLimitItem) {
    setEditingCategory(item.category);
    setDraftCategory(item.category);
    setDraftAmount(String(item.limit_amount));
    setDraftDescription(item.description_my ?? "");
    setDraftBeSeksyen(item.be_seksyen ?? "");
    setDraftSortOrder(String(item.sort_order));
    setDraftIsActive(item.is_active);
  }

  function saveEdit() {
    const formData = new FormData();
    formData.set("category", draftCategory);
    formData.set("limit_amount", draftAmount);
    formData.set("description_my", draftDescription);
    formData.set("be_seksyen", draftBeSeksyen);
    formData.set("sort_order", draftSortOrder);
    formData.set("is_active", draftIsActive ? "true" : "false");

    startTransition(() => {
      updateAction(formData);
      setEditingCategory(null);
    });
  }

  function submitCreate() {
    const formData = new FormData();
    formData.set("category", newCategory);
    formData.set("limit_amount", newAmount);
    formData.set("description_my", newDescription);
    formData.set("be_seksyen", newBeSeksyen);
    if (newSortOrder) {
      formData.set("sort_order", newSortOrder);
    }

    startTransition(() => {
      createAction(formData);
      setShowCreateForm(false);
      setNewCategory("");
      setNewAmount("");
      setNewDescription("");
      setNewBeSeksyen("");
      setNewSortOrder("");
    });
  }

  function deactivate(category: string) {
    if (!window.confirm(`Deactivate relief limit "${category}"?`)) {
      return;
    }

    const formData = new FormData();
    formData.set("category", category);

    startTransition(() => {
      deactivateAction(formData);
      setEditingCategory(null);
    });
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="space-y-1">
          <CardTitle>Relief Limits</CardTitle>
          <CardDescription>
            Manage global claim limits by Borang BE category. These limits apply
            to all tax years.
          </CardDescription>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setShowCreateForm((value) => !value)}
        >
          {showCreateForm ? "Cancel" : "Add"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {feedback ? (
          <p
            className={`text-sm ${
              createState.error || updateState.error || deactivateState.error
                ? "text-destructive"
                : "text-emerald-600"
            }`}
          >
            {feedback}
          </p>
        ) : null}

        {showCreateForm ? (
          <div className="rounded-lg border px-3 py-3 space-y-2">
            <p className="font-medium text-sm">New relief limit</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="new-category">Category slug</Label>
                <Input
                  id="new-category"
                  value={newCategory}
                  onChange={(event) => setNewCategory(event.target.value)}
                  placeholder="e.g. medical_insurance"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="new-amount">Limit (RM)</Label>
                <Input
                  id="new-amount"
                  type="number"
                  min={0}
                  step="0.01"
                  value={newAmount}
                  onChange={(event) => setNewAmount(event.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="new-be-seksyen">BE section</Label>
                <Input
                  id="new-be-seksyen"
                  value={newBeSeksyen}
                  onChange={(event) => setNewBeSeksyen(event.target.value)}
                  placeholder="S.46(1)(b)"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="new-sort-order">Sort order</Label>
                <Input
                  id="new-sort-order"
                  type="number"
                  min={0}
                  value={newSortOrder}
                  onChange={(event) => setNewSortOrder(event.target.value)}
                />
              </div>
              <div className="space-y-1 sm:col-span-2">
                <Label htmlFor="new-description">Description</Label>
                <Input
                  id="new-description"
                  value={newDescription}
                  onChange={(event) => setNewDescription(event.target.value)}
                  placeholder="Medical & Dental"
                />
              </div>
            </div>
            <Button
              type="button"
              size="sm"
              disabled={isPending}
              onClick={submitCreate}
            >
              Save new limit
            </Button>
          </div>
        ) : null}

        {limits.map((item) => {
          const isEditing = editingCategory === item.category;

          return (
            <div
              key={item.id}
              className={`rounded-lg border px-3 py-3 space-y-2 ${
                item.is_active ? "" : "opacity-60"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium">
                    {item.description_my || getCategoryLabel(item.category)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {item.category}
                    {!item.is_active ? " · inactive" : ""}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {item.be_seksyen ?? "—"} · {formatRinggit(item.limit_amount)}
                  </p>
                </div>
                {!isEditing ? (
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => startEdit(item)}
                    >
                      Edit
                    </Button>
                    {item.is_active ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={isPending}
                        onClick={() => deactivate(item.category)}
                      >
                        Deactivate
                      </Button>
                    ) : null}
                  </div>
                ) : null}
              </div>

              {isEditing ? (
                <div className="grid gap-2 sm:grid-cols-2">
                  <Input
                    type="number"
                    min={0}
                    step="0.01"
                    value={draftAmount}
                    onChange={(event) => setDraftAmount(event.target.value)}
                    placeholder="Limit (RM)"
                  />
                  <Input
                    value={draftBeSeksyen}
                    onChange={(event) => setDraftBeSeksyen(event.target.value)}
                    placeholder="BE section"
                  />
                  <Input
                    value={draftDescription}
                    onChange={(event) =>
                      setDraftDescription(event.target.value)
                    }
                    placeholder="Description"
                  />
                  <Input
                    type="number"
                    min={0}
                    value={draftSortOrder}
                    onChange={(event) => setDraftSortOrder(event.target.value)}
                    placeholder="Sort order"
                  />
                  <div className="flex items-center gap-2 sm:col-span-2">
                    <input
                      id={`active-${item.category}`}
                      type="checkbox"
                      className="size-4 rounded border"
                      checked={draftIsActive}
                      onChange={(event) =>
                        setDraftIsActive(event.target.checked)
                      }
                    />
                    <Label htmlFor={`active-${item.category}`}>Active</Label>
                  </div>
                  <div className="flex gap-2 sm:col-span-2">
                    <Button
                      type="button"
                      size="sm"
                      disabled={isPending}
                      onClick={saveEdit}
                    >
                      Save
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setEditingCategory(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
