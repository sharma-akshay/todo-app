import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class TodoService {

  private API = 'http://localhost:3000/api/todos';

  constructor(private http: HttpClient) {}

  getTodos() { return this.http.get<any[]>(this.API); }
  addTodo(text: string) { return this.http.post(this.API, { text }); }
  updateTodo(id: number, completed: boolean) { return this.http.put(`${this.API}/${id}`, { completed }); }
  deleteTodo(id: number) { return this.http.delete(`${this.API}/${id}`); }
}
