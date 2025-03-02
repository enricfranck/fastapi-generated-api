document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("canvas");
    const addEntityBtn = document.getElementById("add-entity");
    const modal = document.getElementById("item-modal");
    const fieldType = document.getElementById("field-type");
    const stringOptions = document.getElementById("string-options");
    const saveItemBtn = document.getElementById("save-item");
    const cancelItemBtn = document.getElementById("cancel-item");
    const fieldNameInput = document.getElementById("field-name");
    const stringLengthInput = document.getElementById("string-length");
    const primaryKeyCheckbox = document.getElementById("primary-key");
    const foreignKeyCheckbox = document.getElementById("foreign-key");

    let isDragging = false;
    let currentEntity = null;
    let offsetX, offsetY;

    // Function to add an entity
    addEntityBtn.addEventListener("click", () => {
        const entity = document.createElement("div");
        entity.classList.add("entity");
        entity.dataset.id = Date.now(); // Unique ID for each entity

        const titleInput = document.createElement("input");
        titleInput.type = "text";
        titleInput.placeholder = "Title";
        entity.appendChild(titleInput);

        const list = document.createElement("ul");

        const addListItemButton = document.createElement("button");
        addListItemButton.textContent = "Add Item";
        addListItemButton.addEventListener("click", () => {
            currentEntity = entity;
            modal.classList.remove("hidden");
        });

        const deleteEntityButton = document.createElement("button");
        deleteEntityButton.textContent = "Delete";
        deleteEntityButton.addEventListener("click", () => {
            canvas.removeChild(entity);
        });

        entity.appendChild(addListItemButton);
        entity.appendChild(deleteEntityButton);
        entity.appendChild(list);
        canvas.appendChild(entity);

        entity.addEventListener("mousedown", (e) => {
            isDragging = true;
            currentEntity = entity;
            offsetX = e.offsetX;
            offsetY = e.offsetY;
        });
    });

    // Handle field type change
    fieldType.addEventListener("change", () => {
        if (fieldType.value === "str") {
            stringOptions.classList.remove("hidden");
        } else {
            stringOptions.classList.add("hidden");
        }
    });

    // Save Diagram to JSON
    const saveBtn = document.getElementById("save");
    saveBtn.addEventListener("click", () => {
        const entities = Array.from(document.querySelectorAll(".entity")).map((entity) => {
            const title = entity.querySelector("input[type='text']").value;
            const items = Array.from(entity.querySelectorAll("ul li")).map((li) => ({
                name: li.dataset.name,
                type: li.dataset.type,
                isPrimaryKey: li.dataset.isPrimaryKey === "true",
                ...(li.dataset.type === "str" && li.dataset.stringLength
                    ? { stringLength: parseInt(li.dataset.stringLength, 10) }
                    : {}),
            }));
            const x = parseInt(entity.style.left.replace("px", ""), 10) || 0;
            const y = parseInt(entity.style.top.replace("px", ""), 10) || 0;

            return { title, items, x, y };
        });

        const blob = new Blob([JSON.stringify(entities, null, 2)], {
            type: "application/json",
        });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "diagram.json";
        link.click();
    });

    // Load Diagram from JSON File
    const loadInput = document.getElementById("load");
    loadInput.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const entities = JSON.parse(e.target.result);

            // Clear the canvas
            document.getElementById("canvas").innerHTML = "";

            // Recreate entities and their items
            entities.forEach((entityData) => {
                const entity = document.createElement("div");
                entity.classList.add("entity");
                entity.style.left = `${entityData.x}px`;
                entity.style.top = `${entityData.y}px`;

                const titleInput = document.createElement("input");
                titleInput.type = "text";
                titleInput.value = entityData.title;
                entity.appendChild(titleInput);

                const list = document.createElement("ul");
                entityData.items.forEach((itemData) => {
                    const listItem = document.createElement("li");
                    listItem.dataset.name = itemData.name;
                    listItem.dataset.type = itemData.type;
                    listItem.dataset.isPrimaryKey = itemData.isPrimaryKey;
                    if (itemData.stringLength) {
                        listItem.dataset.stringLength = itemData.stringLength;
                    }
                    listItem.textContent = `${itemData.name} (${itemData.type})${itemData.isPrimaryKey ? " [PK]" : ""}${
                        itemData.type === "str" && itemData.stringLength ? ` [Length: ${itemData.stringLength}]` : ""
                    }`;

                    // Reattach click event to edit
                    listItem.addEventListener("click", () => {
                        fieldNameInput.value = listItem.dataset.name;
                        fieldType.value = listItem.dataset.type;
                        stringLengthInput.value = listItem.dataset.stringLength || "";
                        primaryKeyCheckbox.checked = listItem.dataset.isPrimaryKey === "true";

                        saveItemBtn.dataset.editingItem = listItem.dataset.id;
                        modal.classList.remove("hidden");
                    });

                    list.appendChild(listItem);
                });

                const addListItemButton = document.createElement("button");
                addListItemButton.textContent = "Add Item";
                addListItemButton.addEventListener("click", () => {
                    currentEntity = entity;
                    modal.classList.remove("hidden");
                });

                const deleteEntityButton = document.createElement("button");
                deleteEntityButton.textContent = "Delete";
                deleteEntityButton.addEventListener("click", () => {
                    canvas.removeChild(entity);
                });

                entity.appendChild(addListItemButton);
                entity.appendChild(deleteEntityButton);
                entity.appendChild(list);
                document.getElementById("canvas").appendChild(entity);

                // Enable dragging
                entity.addEventListener("mousedown", (e) => {
                    isDragging = true;
                    currentEntity = entity;
                    offsetX = e.offsetX;
                    offsetY = e.offsetY;
                });
            });
        };

        reader.readAsText(file);
    });

    // Save item logic
    saveItemBtn.addEventListener("click", () => {
        if (!currentEntity) {
            alert("Error: No entity selected to add the item.");
            return;
        }

        const fieldName = fieldNameInput.value.trim();
        const fieldTypeValue = fieldType.value;
        const stringLength = fieldTypeValue === "str" ? stringLengthInput.value.trim() : null;
        const isPrimaryKey = primaryKeyCheckbox.checked;
        const isForeignKey = foreignKeyCheckbox.checked;

        if (fieldName === "") {
            alert("Field name is required!");
            return;
        }

        let listItem;

        // Check if editing an existing item
        if (saveItemBtn.dataset.editingItem) {
            listItem = document.querySelector(`[data-id="${saveItemBtn.dataset.editingItem}"]`);
            saveItemBtn.removeAttribute("data-editingItem");
        } else {
            listItem = document.createElement("li");
            listItem.dataset.id = Date.now(); // Unique ID for tracking
            listItem.addEventListener("click", () => {
                // Open modal with existing item's data
                fieldNameInput.value = listItem.dataset.name;
                fieldType.value = listItem.dataset.type;
                stringLengthInput.value = listItem.dataset.stringLength || "";
                primaryKeyCheckbox.checked = listItem.dataset.isPrimaryKey === "true";
                foreignKeyCheckbox.checked = listItem.dataset.isForeignKey === "true";

                saveItemBtn.dataset.editingItem = listItem.dataset.id;
                modal.classList.remove("hidden");
            });
            currentEntity.querySelector("ul").appendChild(listItem);
        }

        // Update data attributes
        listItem.dataset.name = fieldName;
        listItem.dataset.type = fieldTypeValue;
        listItem.dataset.isPrimaryKey = isPrimaryKey;
        listItem.dataset.isForeignKey = isForeignKey;
        if (stringLength) {
            listItem.dataset.stringLength = stringLength;
        }

        // Update display text
        listItem.textContent = `${fieldName} (${fieldTypeValue})${isPrimaryKey ? " [PK]" : ""}${isForeignKey ? " [FK]" : ""}`;
        if (stringLength) {
            listItem.textContent += ` [Length: ${stringLength}]`;
        }

        // Hide modal and reset inputs
        modal.classList.add("hidden");
        fieldNameInput.value = "";
        stringLengthInput.value = "";
        primaryKeyCheckbox.checked = false;
        foreignKeyCheckbox.checked = false;
    });

    // Cancel modal
    cancelItemBtn.addEventListener("click", () => {
        modal.classList.add("hidden");
        fieldNameInput.value = "";
        stringLengthInput.value = "";
        primaryKeyCheckbox.checked = false;
        foreignKeyCheckbox.checked = false;
    });

    // Dragging functionality
    canvas.addEventListener("mousemove", (e) => {
        if (isDragging && currentEntity) {
            currentEntity.style.left = `${e.clientX - offsetX}px`;
            currentEntity.style.top = `${e.clientY - offsetY}px`;
        }
    });

    canvas.addEventListener("mouseup", () => {
        if (!modal.classList.contains("hidden")) return;
        isDragging = false;
        currentEntity = null;
    });

    canvas.addEventListener("mouseleave", () => {
        if (!modal.classList.contains("hidden")) return;
        isDragging = false;
        currentEntity = null;
    });
});