// document-count-widget.component.ts
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-document-count-widget',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule
  ],
  template: `
    <mat-card class="count-widget" *ngIf="count > 0">
      <mat-card-content>
        <div class="count-content">
          <mat-icon class="count-icon">description</mat-icon>
          <div class="count-info">
            <div class="count-number">{{count | number}}</div>
            <div class="count-label">Documentos encontrados</div>
          </div>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .count-widget {
      max-width: 300px;
      background-color: #f5f5f5;
      border-radius: 8px;
      transition: all 0.3s ease;
    }

    .count-content {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
    }

    .count-icon {
      font-size: 2rem;
      width: 2rem;
      height: 2rem;
      color: #1976d2;
    }

    .count-info {
      display: flex;
      flex-direction: column;
    }

    .count-number {
      font-size: 1.5rem;
      font-weight: bold;
      color: #1976d2;
    }

    .count-label {
      font-size: 0.875rem;
      color: #666;
    }

    .count-widget:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
  `]
})
export class DocumentCountWidgetComponent {
  @Input() count: number = 0;
  
}