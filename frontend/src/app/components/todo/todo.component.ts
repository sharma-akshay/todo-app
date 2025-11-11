import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TodoService } from '../../services/todo.service';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-todo',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './todo.component.html'
})
export class TodoComponent implements OnInit {
  todos: any[] = [];
  newTodoText = '';

  constructor(private todoService: TodoService) {}

  ngOnInit() { this.load(); }

  load() {
    this.todoService.getTodos().subscribe(data => this.todos = data);
  }

  addTodo() {
    if (!this.newTodoText.trim()) return;
    this.todoService.addTodo(this.newTodoText).subscribe(() => {
      this.newTodoText = '';
      this.load();
    });
  }

  toggle(todo: any) {
    this.todoService.updateTodo(todo.id, !todo.completed).subscribe(() => this.load());
  }

  remove(id: number) {
    this.todoService.deleteTodo(id).subscribe(() => this.load());
  }
}
