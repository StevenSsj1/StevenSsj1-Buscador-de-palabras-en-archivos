import { Component } from '@angular/core';
import { DocumentSearchComponent } from './components/table-documents/table-documents.component';
import { FileUploadComponent } from './components/upload-file-button/upload-file-button.component';
import { HttpClientModule } from '@angular/common/http'; // Asegúrate de importar HttpClientModule
import { DocumentCountWidgetComponent } from './components/widget-documents/document-count-widget.component';
import { DocumentService } from './services/documents-search.service';
import { OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { OnDestroy } from '@angular/core';

@Component({
  selector: 'app-home',
  imports: [DocumentSearchComponent, FileUploadComponent, HttpClientModule, DocumentCountWidgetComponent],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent implements OnInit, OnDestroy {
  documentCount: number = 0;
  private subscription!: Subscription;

  constructor(private documentService: DocumentService) {}

  ngOnInit(): void {
    this.subscription = this.documentService.documentCount$.subscribe(
      count => {
        this.documentCount = count;
        console.log('Document Count:', this.documentCount);
      }
    );

    // Realiza una búsqueda inicial para actualizar el conteo
    this.documentService.searchDocuments('').subscribe();
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
