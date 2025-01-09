export interface DocumentData {
    _id: string;
    _source: {
      name_document: string;
      content: string;
      page_number: number;
      total_pages: number;
    }
  }