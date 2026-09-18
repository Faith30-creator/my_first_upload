import json
from datetime import datetime
from pathlib import Path

# ==================== ENTRY CLASS ====================
class Entry:
    def __init__(self, title, content, date=None):
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.title = title
        self.content = content
    
    def to_dict(self):
        return {
            "date": self.date,
            "title": self.title,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["title"], data["content"], data["date"])
    
    def display(self):
        print("\n" + "="*60)
        print(f"Date: {self.date}")
        print(f"Title: {self.title}")
        print("-" * 60)
        print(self.content)
        print("="*60)


# ==================== JOURNAL CLASS ====================
class Journal:
    def __init__(self, filename="journal_entries.json"):
        self.entries = []
        self.filename = filename
        self.load_entries()
    
    def save_entries(self):
        try:
            data = [entry.to_dict() for entry in self.entries]
            with open(self.filename, "w") as f:
                json.dump(data, f, indent=4)
        except:
            pass  # Fail silently if can't save
    
    def load_entries(self):
        try:
            if Path(self.filename).exists():
                with open(self.filename, "r") as f:
                    data = json.load(f)
                    self.entries = [Entry.from_dict(item) for item in data]
        except:
            self.entries = []
    
    def add_entry(self):
        print("\n--- New Journal Entry ---")
        title = input("Enter title: ").strip()
        content = input("Write your entry:\n")
        
        new_entry = Entry(title, content)
        self.entries.append(new_entry)
        self.save_entries()
        print("✅ Entry saved successfully!")
    
    def view_all_entries(self):
        if not self.entries:
            print("\nNo entries found. Start writing!")
            return
        
        print(f"\n📖 Your Journal ({len(self.entries)} entries)")
        for i, entry in enumerate(self.entries, 1):
            print(f"{i}. {entry.date} - {entry.title}")
    
    def view_entry(self):
        self.view_all_entries()
        if not self.entries:
            return
        try:
            num = int(input("\nEnter entry number to read: "))
            if 1 <= num <= len(self.entries):
                self.entries[num-1].display()
            else:
                print("Invalid number!")
        except:
            print("Please enter a valid number.")
    
    def delete_entry(self):
        self.view_all_entries()
        if not self.entries:
            return
        try:
            num = int(input("\nEnter entry number to DELETE: "))
            if 1 <= num <= len(self.entries):
                deleted = self.entries.pop(num-1)
                self.save_entries()
                print(f"🗑️ Entry '{deleted.title}' has been deleted.")
            else:
                print("Invalid number!")
        except:
            print("Please enter a valid number.")
    
    def menu(self):
        while True:
            print("\n" + "="*50)
            print("      MY PERSONAL JOURNAL")
            print("="*50)
            print("1. Write new entry")
            print("2. View all entries")
            print("3. Read specific entry")
            print("4. Delete an entry")
            print("5. Exit")
            print("="*50)
            
            choice = input("Choose an option (1-5): ").strip()
            
            if choice == "1":
                self.add_entry()
            elif choice == "2":
                self.view_all_entries()
            elif choice == "3":
                self.view_entry()
            elif choice == "4":
                self.delete_entry()
            elif choice == "5":
                self.save_entries()
                print("Goodbye! Your entries have been saved ❤️")
                break
            else:
                print("Invalid choice. Try again.")


# ==================== RUN THE PROGRAM ====================
if __name__ == "__main__":
    my_journal = Journal()   # This will auto-load previous entries
    my_journal.menu()