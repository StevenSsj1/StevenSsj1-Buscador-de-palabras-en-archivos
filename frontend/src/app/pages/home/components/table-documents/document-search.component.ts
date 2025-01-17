import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';

interface DialogData {
  status: string;
  total_found: number;
  total_processed: number;
  processed_files: string[];
  failed_files: Array<{ path: string, error: string }>;
}

@Component({
  selector: 'app-file-detection-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Resultado de la Detección</h2>
    <mat-dialog-content class="dialog-content">
      <div class="results-summary">
        <p><strong>Estado:</strong> {{ data.status === 'success' ? 'Éxito' : 'Error' }}</p>
        <p><strong>Archivos encontrados:</strong> {{ data.total_found }}</p>
        <p><strong>Archivos procesados:</strong> {{ data.total_processed }}</p>
      </div>

      <div *ngIf="getProcessedFiles().length > 0" class="files-section">
        <h3>Archivos Procesados:</h3>
        <ul>
          <li *ngFor="let file of getProcessedFiles()">{{ file }}</li>
        </ul>
      </div>

      <div *ngIf="getFailedFiles().length > 0" class="files-section error-section">
        <h3>Archivos con Errores:</h3>
        <ul>
          <li *ngFor="let file of getFailedFiles()">
            {{ file.path }} - Error: {{ file.error }}
          </li>
        </ul>
      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="close()">Cerrar</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .dialog-content {
      min-width: 300px;
      max-width: 500px;
      max-height: 400px;
      overflow-y: auto;
    }

    .results-summary {
      margin-bottom: 20px;
    }

    .files-section {
      margin-top: 15px;
    }

    .files-section h3 {
      margin-bottom: 10px;
      color: #333;
    }

    .error-section {
      color: #dc3545;
    }

    ul {
      list-style-type: none;
      padding-left: 0;
    }

    li {
      margin-bottom: 5px;
      word-break: break-all;
    }
  `]
})
export class FileDetectionDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<FileDetectionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {}

  getProcessedFiles(): string[] {
    return this.data.processed_files || [];
  }

  getFailedFiles(): Array<{ path: string, error: string }> {
    return this.data.failed_files || [];
  }

  close(): void {
    this.dialogRef.close();
  }
}